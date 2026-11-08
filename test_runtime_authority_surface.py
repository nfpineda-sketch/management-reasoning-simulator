"""P3-26 and P3-27: the faculty failure surface, the artifact store, and halt semantics.

Faculty decision of 2026-11-07 (decision F): a hard authority failure must be visible immediately on a
faculty/development surface, must never be a resident-facing clinical event, must never fall back silently
to legacy, and must halt the experiment for that encounter -- preserving every committed minute exactly as
it happened. The artifact lives in a separate Phase-3 faculty/research surface, outside the frozen Phase-2
schemas, the resident trace, the scoring data and the critical-event data.

Nothing here enables authority: the registry is empty, the injection goes through the private mapping the
production scan watches, and the store is off unless a faculty environment names a directory.
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
TEST_ONLY_SNAPSHOT = {"id": "test_only_surface_point",
                      "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
                      "parameters": {"test_only_placeholder": 1.0}}
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY,
        ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"],
        ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE}


#: This file's own artifact store, outside the repository: no test here may write into an ambient one.
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-surface-")


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    """No authority test may write into an ambient faculty store (P3-28 review)."""
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)


@pytest.fixture
def approved(monkeypatch, tmp_path):
    """The test-only approval and a faculty store directory, both gone when the test ends."""
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    directory = tmp_path / "phase3_authority"
    monkeypatch.setenv(store.STORE_FLAG, str(directory))
    return {"snapshot": TEST_ONLY_SNAPSHOT, "store": directory,
            "environ": {**BEST, store.STORE_FLAG: str(directory)}}


@pytest.fixture
def gi_turn():
    """A real GI encounter with one settled turn and its live shadow session."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    return {"arrival": arrival, "state": deepcopy(encounter.state), "session": encounter.shadow,
            "ran": [dict(order) for order in encounter.entries[-1]["orders"]], "encounter": encounter}


def _site(approved, gi_turn):
    return ra.open_site(gi_turn["arrival"], environ=approved["environ"])


def _minute(site, gi_turn, *, ran=None, state=None, submission="t0"):
    return site.minute(None, state or deepcopy(gi_turn["state"]), gi_turn["session"],
                       gi_turn["ran"] if ran is None else ran, submission)


class _Recorder:
    """The smallest Streamlit the faculty surface needs, so what it draws can be read back."""

    def __init__(self, session_state):
        self.session_state = session_state
        self.drawn = []

    class _Block:
        def __init__(self, outer):
            self.outer = outer

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def expander(self, label, expanded=False):
        self.drawn.append(("expander", label, expanded))
        return self._Block(self)

    def json(self, payload):
        self.drawn.append(("json", payload))

    def error(self, text):
        self.drawn.append(("error", str(text)))

    def caption(self, text):
        self.drawn.append(("caption", str(text)))

    def __getattr__(self, name):  # anything else the surface might touch is a failure, not a no-op
        raise AssertionError(f"the faculty surface used st.{name}, which this test does not allow")


def _render(session_state, monkeypatch):
    import app
    recorder = _Recorder(session_state)
    monkeypatch.setattr(app, "st", recorder)
    app._render_authority_experiment()
    return recorder.drawn


# -- P3-26-1, P3-26-2: the status reader and the faculty-only surface ----------------------------------

def test_s1_the_surface_reads_the_status_and_derives_nothing():
    """P3-26-1: one structured source. The surface may read it and render it, and compute nothing."""
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    surface = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                   and node.name == "_render_authority_experiment")
    calls = sorted({ast.unparse(node.func) for node in ast.walk(surface) if isinstance(node, ast.Call)})
    assert calls == ["_authority_layer.authority_status", "_authority_store.records", "bool",
                     "st.caption", "st.error", "st.expander", "st.json", "status.get", "str"], calls
    # It reads the layer's own constants instead of repeating their text. The docstring is dropped: what
    # the code does is the claim, not what it says about itself.
    body = [node for node in surface.body
            if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))]
    source = "\n".join(ast.unparse(node) for node in body)
    for name in ("EXPERIMENT_NOT_STARTED", "INVALID_FOR_CONTINUATION", "FAILURE_POLICY"):
        assert f"_authority_layer.{name}" in source, name
    # And it names no clinical field at all: a surface that read a vital or the score would be deriving
    # clinical state instead of rendering a status.
    for forbidden in ("sbp", "dbp", '"map"', "observable", "score", "hidden", "treatments",
                      "management_trace", "events"):
        assert forbidden not in source, forbidden
    # The only session key it touches is the one the status reader takes.
    assert source.count("st.session_state") == 1


def test_s2_the_surface_is_drawn_only_behind_the_faculty_gate():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    callers = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
               and "_render_authority_experiment()" in ast.unparse(node)
               and node.name != "_render_authority_experiment"]
    assert [node.name for node in callers] == ["_render_staff_tools"], [n.name for n in callers]
    # Every call of the staff tools is inside a faculty_access() condition.
    guards = [node for node in ast.walk(tree) if isinstance(node, ast.If)
              and any(ast.unparse(statement).strip() == "_render_staff_tools()"
                      for statement in node.body)]
    assert len(guards) == 2, [ast.unparse(node.test) for node in guards]
    for node in guards:
        assert "faculty_access()" in ast.unparse(node.test), ast.unparse(node.test)


def test_s3_nothing_is_drawn_without_an_experiment(monkeypatch):
    assert _render({}, monkeypatch) == []
    assert _render({ra.SITE_KEY: None, ra.ARTIFACT_KEY: None}, monkeypatch) == []


def test_s4_a_halted_experiment_is_drawn_with_its_exact_reason(approved, gi_turn, monkeypatch):
    site = _site(approved, gi_turn)
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert _minute(site, gi_turn, ran=ran) is None and site.halted
    session_state = {ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()}
    drawn = _render(session_state, monkeypatch)
    kinds = [item[0] for item in drawn]
    assert kinds[0] == "expander" and "HALTED" in drawn[0][1]
    assert drawn[0][2] is True, "a halted experiment opens the panel"
    errors = [item[1] for item in drawn if item[0] == "error"]
    assert errors and ra.INVALID_FOR_CONTINUATION in errors[0]
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in errors[0], errors
    assert "norepinephrine" in errors[0], "the reason names the class, not only the validation key"
    payload = [item[1] for item in drawn if item[0] == "json"][0]
    for key in ("mode", "experiment_state", "snapshot_id", "authority_domain", "minute", "outcome",
                "failure_reason", "unsupported_actions", "authority_minutes", "mixed_trajectory",
                "legacy_counterfactual_available", "artifact_id", "artifact_digest", "stored",
                "case_id", "attempt", "environment"):
        assert key in payload, key
    assert payload["experiment_state"] == ra.EXPERIMENT_HALTED
    assert payload["snapshot_id"] == TEST_ONLY_SNAPSHOT["id"]
    assert payload["authority_domain"] == list(ra.AUTHORITY_DOMAIN)
    assert payload["legacy_counterfactual_available"] is True
    # No resident wording and no clinical event: the panel is a developer panel.
    text = json.dumps(drawn, default=str)
    for forbidden in ("mmHg", "patient", "paciente", "vital", "deteriorat"):
        assert forbidden not in text, forbidden


@pytest.mark.parametrize("injection,expected", [
    ("unsupported", ra.UNSUPPORTED_AUTHORITY_ACTION),
    ("invalid_snapshot", "snapshot_approved"),
    ("digest_mismatch", "minute_reproducible"),
    ("replay_mismatch", "minute_reproducible"),
    ("core_failure", "no_core_failure"),
    ("boundary", "no_unresolved_boundary"),
    ("validation", "invariants_hold"),
    ("partial_transaction", "the write failed half way"),
    ("no_candidate", ra.NO_COMMON_CANDIDATE),
])
def test_s5_every_failure_is_shown_with_its_structured_reason(approved, gi_turn, monkeypatch,
                                                              injection, expected):
    """P3-26-3: no generic silent 'error' when the structured reason is known."""
    site = _site(approved, gi_turn)
    ran, state = list(gi_turn["ran"]), deepcopy(gi_turn["state"])
    if injection == "unsupported":
        ran.append({"order_id": "t0:9", "class": "aspirin", "fate": "EXECUTED"})
    elif injection == "invalid_snapshot":
        site.snapshot = {"id": "forged"}
    elif injection in ("digest_mismatch", "replay_mismatch"):
        monkeypatch.setattr(ra.AuthoritySite, "_replayed_point",
                            staticmethod(lambda artifact, minute: {"sbp": 1.0, "dbp": 1.0, "map": 1.0}))
    elif injection in ("core_failure", "boundary"):
        classification = rs.UNEXPECTED if injection == "core_failure" else rs.BOUNDARY
        gi_turn["session"].failures.append(rs.ShadowFailure(
            max(gi_turn["session"].runner.compared), "core", "CoreInvariantError", "x", classification))
    elif injection == "validation":
        original = ra.AuthorityTransaction.validate
        monkeypatch.setattr(ra.AuthorityTransaction, "validate",
                            lambda self, **kwargs: original(self, **{**kwargs,
                                                                     "invariants_hold": False}))
    elif injection == "partial_transaction":
        def boom(self, target, *, environ=None):
            raise RuntimeError("the write failed half way")
        monkeypatch.setattr(ra.AuthorityTransaction, "commit", boom)
    elif injection == "no_candidate":
        state = {**state, "sim_time": 9999}
    try:
        prepared = _minute(site, gi_turn, ran=ran, state=state)
    finally:
        if injection in ("core_failure", "boundary"):
            gi_turn["session"].failures.pop()
    assert prepared is None and site.halted
    status = ra.authority_status({ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()})
    reason = f'{status["failure_reason"]} {status["halt_reason"]}'
    assert expected in reason, (injection, reason)
    assert status["experiment_state"] == ra.EXPERIMENT_HALTED
    assert reason.strip() not in ("", "error", "Error"), injection
    drawn = _render({ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()}, monkeypatch)
    assert any(expected in str(item[1]) for item in drawn if item[0] in ("error", "json")), injection


# -- P3-26-4, P3-26-5, P3-26-6: the store ---------------------------------------------------------------

def test_s6_every_outcome_is_persisted(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    assert dict(site.stored)["stored"] is True, site.stored
    committed = store.records(environ=approved["environ"])
    assert len(committed) == 1 and committed[0]["minutes"] == 1
    assert committed[0]["experiment_state"] == ra.EXPERIMENT_ACTIVE
    # A refusal of the same minute, a halt, and both are stored as their own records.
    assert _minute(site, gi_turn) is None
    rows = store.records(environ=approved["environ"])
    assert len(rows) == 2, rows
    assert rows[-1]["halted"] is True and rows[-1]["experiment_state"] == ra.EXPERIMENT_HALTED
    assert rows[-1]["mixed_trajectory"] is True
    # Writing the same artifact again is idempotent, and nothing is ever overwritten.
    again = store.persist(site.artifact(), environ=approved["environ"])
    assert again["stored"] and again["idempotent"]
    assert len(store.records(environ=approved["environ"])) == 2


def test_s7_production_persists_nothing(gi_turn, monkeypatch, tmp_path):
    monkeypatch.delenv(store.STORE_FLAG, raising=False)
    assert store.root() is None and not store.configured()
    assert store.persist({"artifact": "phase3_authority_experiment"})["why"] == store.NOT_CONFIGURED
    assert store.records() == [] and store.paths() == []
    assert store.load("whatever") is None
    assert not list(tmp_path.iterdir())


def test_s8_the_identity_is_deterministic_and_distinguishes_what_it_must(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    artifact = site.artifact()
    first = store.artifact_id(artifact)
    assert first == store.artifact_id(json.loads(json.dumps(artifact, default=str)))
    assert len(first) == 32
    for field, value in (("encounter_id", "another-encounter"), ("attempt", 2), ("experiment_id", "x"),
                         ("case_id", "gi_bleed_72f"), ("site", "P9-99")):
        assert store.artifact_id({**artifact, field: value}) != first, field
    # A second minute is a different record, and no clock is involved anywhere.
    source = (ROOT / "runtime_authority_store.py").read_text(encoding="utf-8")
    for forbidden in ("time.time", "datetime", "uuid", "random"):
        assert forbidden not in source, forbidden


def test_s9_persistence_mutates_nothing_else(approved, gi_turn):
    import management_trace_store
    encounter = gi_turn["encounter"]
    state = deepcopy(gi_turn["state"])
    before = {
        "state": ra.digest_of(state),
        "entries": ra.digest_of([dict(entry) for entry in encounter.entries]),
        "ledger": ra.digest_of([dict(item) for item in encounter.ledger]),
        "payload": ra.digest_of(management_trace_store.analysis_payload_from_session(
            {"state": state, "history": [], "events": [], "management_trace": []})),
    }
    site = _site(approved, gi_turn)
    prepared = site.minute(None, state, gi_turn["session"], gi_turn["ran"], "t0")
    assert prepared is not None and dict(site.stored)["stored"]
    after = {
        "state": ra.digest_of(state),
        "entries": ra.digest_of([dict(entry) for entry in encounter.entries]),
        "ledger": ra.digest_of([dict(item) for item in encounter.ledger]),
        "payload": ra.digest_of(management_trace_store.analysis_payload_from_session(
            {"state": state, "history": [], "events": [], "management_trace": []})),
    }
    assert before == after, "persisting an artifact changed something it does not own"
    # The stored record carries no free text and no resident wording: it adds no PHI of its own.
    stored = json.dumps(store.load(dict(site.stored)["artifact_id"], environ=approved["environ"]))
    for forbidden in ("raw_text", "learner_input", "normal saline", "Reassess"):
        assert forbidden not in stored, forbidden


def test_s10_only_the_faculty_surface_reads_the_store():
    """One reader outside the layer, in one function, behind the faculty gate -- and nothing else."""
    def imports(path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                 for alias in node.names}
        return names | {node.module for node in ast.walk(tree)
                        if isinstance(node, ast.ImportFrom) and node.module}

    readers = sorted(path.name for path in ROOT.glob("*.py")
                     if not path.name.startswith("test_") and path.name not in rs.LAYER_SOURCES
                     and "runtime_authority_store" in imports(path))
    assert readers == ["app.py"], readers
    # And inside app.py it is one function: the faculty panel, which only the staff tools draw.
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    users = sorted({node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                    and "runtime_authority_store" in ast.unparse(node)})
    assert users == ["_render_authority_experiment"], users
    for name in store.RESIDENT_READERS_FORBIDDEN:
        path = ROOT / name
        if path.exists() and name != "app.py":
            assert "runtime_authority_store" not in path.read_text(encoding="utf-8"), name


# -- P3-26-7, P3-26-8: retrieval, verification and tampering --------------------------------------------

def test_s11_a_stored_artifact_is_retrieved_verified_and_replayed(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    identifier = dict(site.stored)["artifact_id"]
    loaded = store.load(identifier, environ=approved["environ"])
    assert loaded and loaded["artifact_digest"] == site.artifact()["artifact_digest"]
    checked = store.verify(identifier, environ=approved["environ"])
    assert checked["found"] and checked["verified"] and checked["identity_matches"]
    assert "does not detect" in checked["integrity"], "the limit must be stated by the verifier"
    replayed = store.replay(identifier, environ=approved["environ"])
    assert replayed["found"] and replayed["verified"] and replayed["reproduces"]
    assert replayed["compared"] == 1
    assert store.verify("not-an-id", environ=approved["environ"])["found"] is False
    assert store.replay("not-an-id", environ=approved["environ"])["reproduces"] is False


def test_s12_a_tampered_record_fails_verification(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    identifier = dict(site.stored)["artifact_id"]
    path = Path(dict(site.stored)["path"])
    record = json.loads(path.read_text(encoding="utf-8"))
    record["artifact"]["minutes"][0]["written_candidate"] = {"sbp": 999, "dbp": 999, "map": 999}
    path.write_text(json.dumps(record), encoding="utf-8")
    checked = store.verify(identifier, environ=approved["environ"])
    assert checked["found"] and not checked["verified"] and not checked["digest_matches"]
    assert checked["why"] == store.DIGEST_MISMATCH
    assert not store.replay(identifier, environ=approved["environ"])["reproduces"]
    # And the module says exactly what the digest can and cannot do.
    text = (ROOT / "runtime_authority_store.py").read_text(encoding="utf-8")
    assert "does NOT detect a malicious actor" in text


def test_s13_a_record_is_never_overwritten(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    identifier = dict(site.stored)["artifact_id"]
    path = Path(dict(site.stored)["path"])
    artifact = store.load(identifier, environ=approved["environ"])
    forged = {**artifact, "case_id": "gi_bleed_72f"}
    outcome = store.persist(forged, environ=approved["environ"])
    # A different identity is a new record; the original file is untouched either way.
    assert outcome["stored"] and outcome["artifact_id"] != identifier
    assert json.loads(path.read_text(encoding="utf-8"))["artifact"]["case_id"] == CASE
    # The same identity with different content is refused, never written over.
    same_id = {**artifact, "halt_reason": "edited"}
    collision = store.persist(same_id, environ=approved["environ"])
    assert collision["stored"] is False or collision["artifact_id"] != identifier


# -- P3-27: the halt semantics (H1-H8) ------------------------------------------------------------------

def test_h1_a_failure_before_the_first_commit_halts_and_commits_nothing(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert site.experiment_state == ra.EXPERIMENT_ACTIVE
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "class": "norepinephrine", "fate": "EXECUTED"}]
    state = deepcopy(gi_turn["state"])
    assert _minute(site, gi_turn, ran=ran, state=state) is None
    assert site.experiment_state == ra.EXPERIMENT_HALTED and site.minutes_committed == ()
    assert state == deepcopy(gi_turn["state"])
    artifact = site.artifact()
    assert artifact["mixed_trajectory"] is False
    assert artifact["invalid_for_continuation"] == ra.INVALID_FOR_CONTINUATION


def test_h2_a_failure_after_a_commit_preserves_the_commit_and_halts(approved, gi_turn):
    site = _site(approved, gi_turn)
    prepared = _minute(site, gi_turn)
    assert prepared is not None
    committed = dict(site.records[-1])
    advanced = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + 5}
    ran = list(gi_turn["ran"]) + [{"order_id": "t1:0", "class": "aspirin", "fate": "EXECUTED"}]
    assert site.minute(None, advanced, gi_turn["session"], ran, "t1") is None
    assert site.experiment_state == ra.EXPERIMENT_HALTED
    # The committed minute is preserved exactly: no retrospective mutation of history.
    assert dict(site.records[0]) == committed
    assert site.minutes_committed == (committed["minute"],)
    artifact = site.artifact()
    assert artifact["mixed_trajectory"] is True
    assert artifact["authority_minutes"] == [committed["minute"]]
    assert ra.replay_site_artifact(json.loads(json.dumps(artifact, default=str)))["reproduces"]


def test_h3_no_minute_commits_after_a_halt(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    ran = list(gi_turn["ran"]) + [{"order_id": "t1:0", "class": "norepinephrine", "fate": "EXECUTED"}]
    advanced = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + 5}
    assert site.minute(None, advanced, gi_turn["session"], ran, "t1") is None
    for extra in (10, 15, 20):
        later = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + extra}
        assert site.minute(None, later, gi_turn["session"], gi_turn["ran"], f"t{extra}") is None
        assert dict(site.records[-1])["failure_reason"] == ra.SITE_HALTED
    assert len(site.minutes_committed) == 1
    assert site.experiment_state == ra.EXPERIMENT_HALTED


def test_h4_toggling_flags_cannot_resume_a_halted_experiment(approved, gi_turn, monkeypatch):
    site = _site(approved, gi_turn)
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert _minute(site, gi_turn, ran=ran) is None and site.halted
    session_state = {ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()}
    for environ in ({}, BEST, {**BEST, ra.ENVIRONMENT_FLAG: "faculty"}):
        with pytest.MonkeyPatch.context() as patch:
            for name, value in environ.items():
                patch.setenv(name, value)
            same = ra.site_for(gi_turn["state"], session_state, environ=environ or None)
            assert same is None or same is site, "no flag produces a new site for this encounter"
            if same is site:
                assert same.experiment_state == ra.EXPERIMENT_HALTED
                assert _minute(same, gi_turn) is None
    # No code path assigns ACTIVE to an existing site: the state is set once, when a site is built.
    source = (ROOT / "runtime_authority.py").read_text(encoding="utf-8")
    assignments = [line.strip() for line in source.splitlines()
                   if "experiment_state" in line and "=" in line and "==" not in line]
    assert [line for line in assignments if "EXPERIMENT_ACTIVE" in line] == [
        "experiment_state: str = field(default=EXPERIMENT_ACTIVE, init=False)"], assignments


def test_h5_a_new_encounter_gets_an_independent_experiment(approved, gi_turn):
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    site = _site(approved, gi_turn)
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert _minute(site, gi_turn, ran=ran) is None and site.halted
    session_state = {ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()}
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        second = pilot_acceptance.Encounter(CASE, seed=99)
        arrival = deepcopy(second.state)
    fresh = ra.site_for(arrival, session_state, environ=approved["environ"])
    assert fresh is not None and fresh is not site
    assert fresh.experiment_state == ra.EXPERIMENT_ACTIVE and not fresh.halted
    assert fresh.encounter_id != site.encounter_id
    assert session_state[ra.ARTIFACT_KEY] is None, "the previous artifact is dropped with its encounter"
    assert fresh.experiment_id != site.experiment_id


def test_h6_the_replay_reproduces_the_halt(approved, gi_turn):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    advanced = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + 5}
    ran = list(gi_turn["ran"]) + [{"order_id": "t1:0", "class": "anticoagulation", "fate": "EXECUTED"}]
    assert site.minute(None, advanced, gi_turn["session"], ran, "t1") is None
    identifier = dict(site.stored)["artifact_id"]
    replayed = store.replay(identifier, environ=approved["environ"])
    assert replayed["experiment_state"] == ra.EXPERIMENT_HALTED
    assert replayed["mixed_trajectory"] is True
    assert replayed["verified"] and replayed["reproduces"]
    minutes = [row for row in replayed["minutes"] if row["recorded_candidate_digest"]]
    assert len(minutes) == 1, "the committed minute replays; the failed one has no candidate digest"
    stored = store.load(identifier, environ=approved["environ"])
    assert [dict(row)["outcome"] for row in stored["minutes"]] == [ra.COMMITTED, ra.ABORTED]
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in stored["halt_reason"]


def test_h7_the_faculty_surface_shows_the_halt(approved, gi_turn, monkeypatch):
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    advanced = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + 5}
    ran = list(gi_turn["ran"]) + [{"order_id": "t1:0", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert site.minute(None, advanced, gi_turn["session"], ran, "t1") is None
    drawn = _render({ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()}, monkeypatch)
    payload = [item[1] for item in drawn if item[0] == "json"][0]
    assert payload["experiment_state"] == ra.EXPERIMENT_HALTED
    assert payload["mixed_trajectory"] is True
    assert payload["authority_minutes"] == list(site.minutes_committed)
    assert payload["artifact_id"] == dict(site.stored)["artifact_id"]
    assert [item for item in drawn if item[0] == "error"], "a halt must be an error, not a caption"


def test_h8_the_resident_sees_nothing_of_the_experiment(approved, gi_turn):
    """The resident path: a halted experiment in the session changes no vital and no wording."""
    from streamlit.testing.v1 import AppTest
    site = _site(approved, gi_turn)
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert _minute(site, gi_turn, ran=ran) is None and site.halted
    at = AppTest.from_file("app.py", default_timeout=300)
    at.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    at.session_state["_shared_access_granted"] = True
    at.run()
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    begin[0].click().run()
    legacy = dict(at.session_state["state"]["observable"])
    at.session_state[ra.SITE_KEY] = site
    at.session_state[ra.ARTIFACT_KEY] = site.artifact()
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert dict(at.session_state["state"]["observable"]) == legacy, "no vital moved"
    screen = "\n".join(str(item.value) for item in at.markdown)
    for forbidden in (ra.INVALID_FOR_CONTINUATION, ra.UNSUPPORTED_AUTHORITY_ACTION,
                      TEST_ONLY_SNAPSHOT["id"], "authority"):
        assert forbidden not in screen, forbidden
    assert ra.authority_status(at.session_state)["experiment_state"] == ra.EXPERIMENT_HALTED


# -- P3-28 review: what the adversarial pass on this package closed -----------------------------------

def test_s14_a_halt_at_minute_zero_is_not_rebuilt_for_the_same_encounter(approved, gi_turn):
    """The review's hardest finding: a turn that does not move the clock halted, and the next turn got a
    brand-new ACTIVE site for the same patient."""
    site = ra.site_for(gi_turn["arrival"], (session := {}), environ=approved["environ"])
    assert site is not None and session[ra.SITE_KEY] is site
    # A halt at minute 0: the clock has not moved, so ``is_for`` used to drop the site and rebuild it.
    assert site.minute(None, deepcopy(gi_turn["arrival"]), gi_turn["session"], None, "t0") is None
    assert site.halted and site.experiment_state == ra.EXPERIMENT_HALTED
    session[ra.ARTIFACT_KEY] = site.artifact()
    again = ra.site_for(gi_turn["arrival"], session, environ=approved["environ"])
    assert again is None, "no second authority attempt in the same encounter"
    assert session[ra.HALTED_KEY] == site.encounter_id
    assert session[ra.ARTIFACT_KEY] is not None, "the halt's artifact outlives its site"
    status = ra.authority_status(session)
    assert status["experiment_state"] == ra.EXPERIMENT_HALTED
    assert status["halt_reason"]
    # And it stays refused for that encounter, however many turns follow.
    for _ in range(3):
        assert ra.site_for(gi_turn["arrival"], session, environ=approved["environ"]) is None


def test_s15_a_configuration_change_inside_an_encounter_halts_the_experiment(approved, gi_turn,
                                                                            monkeypatch):
    """Faculty decision F: never a silent return to legacy. A flag that disappears is a hard failure."""
    session = {}
    site = ra.site_for(gi_turn["arrival"], session)        # no explicit environ: the live one is used
    assert site is not None and not site.halted
    monkeypatch.delenv(ra.AUTHORITY_FLAG)
    same = ra.site_for(gi_turn["state"], session)
    assert same is site, "the site is not dropped mid-encounter: the mode was decided at the arrival"
    assert same.halted and same.halt_reason == ra.CONFIGURATION_CHANGED
    assert dict(same.records[-1])["failure_reason"] == ra.CONFIGURATION_CHANGED
    assert dict(same.records[-1])["legacy_counterfactual"], "the minute's legacy pressures are kept"
    assert dict(same.stored)["stored"] is True, same.stored
    # A changed snapshot id is the same kind of change.
    monkeypatch.setenv(ra.AUTHORITY_FLAG, ra.MODE_LIMITED_COMMON_AUTHORITY)
    other = {}
    fresh = ra.site_for(gi_turn["arrival"], other)
    assert fresh is not None
    monkeypatch.setenv(ra.SNAPSHOT_FLAG, "another_point")
    assert ra.site_for(gi_turn["state"], other) is fresh
    assert fresh.halted and fresh.halt_reason == ra.CONFIGURATION_CHANGED


def test_s16_an_experiment_with_nowhere_to_record_itself_does_not_start(approved, gi_turn, monkeypatch):
    monkeypatch.delenv(store.STORE_FLAG)
    assert ra.open_site(gi_turn["arrival"]) is None
    assert ra.site_for(gi_turn["arrival"], {}) is None
    # A store named inside the repository is no store at all, so it does not start either.
    monkeypatch.setenv(store.STORE_FLAG, str(ROOT / "docs"))
    assert store.root() is None and ra.open_site(gi_turn["arrival"]) is None
    monkeypatch.setenv(store.STORE_FLAG, str(approved["store"]))
    assert ra.open_site(gi_turn["arrival"]) is not None


def test_s17_an_unsupported_class_is_named_even_when_the_clock_did_not_move(approved, gi_turn):
    """The review: a turn after a committed minute reported only 'minute already committed'."""
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    ran = list(gi_turn["ran"]) + [{"order_id": "t1:0", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert _minute(site, gi_turn, ran=ran) is None
    record = dict(site.records[-1])
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in record["failure_reason"]
    assert "norepinephrine" in record["failure_reason"]
    assert record["unsupported_actions"] == ["norepinephrine"]
    assert ra.MINUTE_ALREADY_COMMITTED not in record["failure_reason"]
    # Without the unsupported class, the same turn is refused for the clock, and says so.
    other = _site(approved, gi_turn)
    assert _minute(other, gi_turn) is not None
    assert _minute(other, gi_turn) is None
    assert ra.MINUTE_ALREADY_COMMITTED in dict(other.records[-1])["failure_reason"]


def test_s18_an_internal_error_preserves_the_same_evidence_as_any_failure(approved, gi_turn,
                                                                         monkeypatch):
    site = _site(approved, gi_turn)
    monkeypatch.setattr(ra.AuthoritySite, "_artifact_input",
                        staticmethod(lambda session: (_ for _ in ()).throw(RuntimeError("boom"))))
    assert _minute(site, gi_turn) is None and site.halted
    record = dict(site.records[-1])
    assert "SITE_ERROR" in record["failure_reason"] and "RuntimeError" in record["failure_reason"]
    assert record["legacy_counterfactual"], "decision F: the legacy counterfactual is preserved"
    assert record["precommit_observable_digest"]
    assert "rollback" in record and record["rollback"]["committed"] == []
    assert dict(site.stored)["stored"] is True


def test_s19_a_vanished_site_with_committed_minutes_reads_as_a_mixed_trajectory(approved, gi_turn):
    """A resumed encounter, or one whose flag was removed, carries common pressures and no site."""
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    artifact = site.artifact()
    assert artifact["mixed_trajectory"] is False, "while the experiment runs it is not mixed yet"
    status = ra.authority_status({ra.ARTIFACT_KEY: artifact})     # the site is gone; the record is not
    assert status["experiment_state"] in (ra.EXPERIMENT_NOT_STARTED, ra.EXPERIMENT_REFUSED,
                                          ra.EXPERIMENT_HALTED)
    assert status["mixed_trajectory"] is True, "committed minutes with no running experiment are mixed"
    assert status["authority_minutes"] == list(site.minutes_committed)


def test_s20_the_replay_verdict_says_what_it_covers(approved, gi_turn):
    """The review: 'reproduces: True' over 1 of 4 minutes read as 'the experiment reproduces'."""
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    for extra in (5, 10):
        later = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + extra}
        assert site.minute(None, later, gi_turn["session"], gi_turn["ran"], f"t{extra}") is None
    artifact = json.loads(json.dumps(site.artifact(), default=str))
    verdict = ra.replay_site_artifact(artifact)
    assert verdict["minutes_recorded"] == 3 and verdict["minutes_committed"] == 1
    assert verdict["compared"] == 1
    assert verdict["covers_every_committed_minute"] is True
    assert verdict["verdict"] == "every committed minute reproduces"
    assert verdict["reproduces"] is True
    # And an artifact with no committed minute does not claim to reproduce anything.
    refused = _site(approved, gi_turn)
    assert refused.minute(None, deepcopy(gi_turn["state"]), gi_turn["session"], None, "t0") is None
    empty = ra.replay_site_artifact(json.loads(json.dumps(refused.artifact(), default=str)))
    assert empty["reproduces"] is False and empty["minutes_committed"] == 0
    assert empty["verdict"] == "no committed minute to reproduce"


def test_s21_the_store_refuses_a_directory_inside_the_repository(approved):
    for named in ("docs", ".", "validation", str(ROOT), str(ROOT / "docs"), str(ROOT / "validation")):
        assert store.root(environ={store.STORE_FLAG: named}) is None, named
        assert store.refused_root(environ={store.STORE_FLAG: named}) == store.OUTSIDE_THE_REPOSITORY
        assert store.persist({"artifact": "phase3_authority_experiment"},
                             environ={store.STORE_FLAG: named})["why"] == store.NOT_CONFIGURED
    assert store.root(environ={store.STORE_FLAG: str(approved["store"])}) is not None
    assert store.refused_root(environ={store.STORE_FLAG: str(approved["store"])}) == ""
    # Nothing was created anywhere in the tree by asking.
    assert not (ROOT / "docs" / "phase3_authority").exists()


def test_s22_a_record_with_the_same_identity_and_different_content_is_refused(approved, gi_turn):
    """With the digest out of the identity, the create-only rule can actually refuse something."""
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    artifact = site.artifact()
    identifier = store.artifact_id(artifact)
    assert dict(site.stored)["artifact_id"] == identifier
    assert store.persist(artifact, environ=approved["environ"])["idempotent"] is True
    edited = {**json.loads(json.dumps(artifact, default=str)), "halt_reason": "edited"}
    assert store.artifact_id(edited) == identifier, "the identity does not depend on the content"
    outcome = store.persist(edited, environ=approved["environ"])
    assert outcome["stored"] is False and outcome["why"] == store.COLLISION
    kept = store.load(identifier, environ=approved["environ"])
    assert kept["halt_reason"] != "edited", "the first record is the record"


def test_s23_no_authority_test_can_write_into_an_ambient_store():
    """Every authority test file pins the store flag, so the repository's suite cannot write into one."""
    files = sorted(path.name for path in ROOT.glob("test_runtime_authority*.py"))
    assert len(files) >= 5, files
    for name in files:
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        pinned = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                  and "STORE_FLAG" in ast.unparse(node)
                  and any("monkeypatch.setenv" in ast.unparse(statement) for statement in node.body)]
        assert pinned, (name, "no fixture pins the artifact store")
        autouse = [node for node in pinned
                   if any("autouse=True" in ast.unparse(item) for item in node.decorator_list)]
        assert autouse, (name, "the pinning is not autouse")


def test_s24_the_surface_falls_back_to_the_stored_records(approved, gi_turn, monkeypatch):
    """A resumed encounter loses the session keys; the durable record is what is left."""
    site = _site(approved, gi_turn)
    assert _minute(site, gi_turn) is not None
    # The session is gone -- a resume, a new browser session -- and the store still has the experiment.
    drawn = _render({}, monkeypatch)
    labels = [item[1] for item in drawn if item[0] == "expander"]
    assert labels and "on record" in labels[0], drawn
    payload = [item[1] for item in drawn if item[0] == "json"][0]
    assert payload and payload[0]["artifact_id"] == dict(site.stored)["artifact_id"]
    assert payload[0]["case_id"] == CASE
    # With no record at all, the surface still draws nothing.
    monkeypatch.setenv(store.STORE_FLAG, str(approved["store"] / "empty"))
    assert _render({}, monkeypatch) == []
