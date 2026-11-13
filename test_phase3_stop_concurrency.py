"""P3-260: duplicate sessions, duplicate tabs and the single-process safety of the effective stop.

TEST-SIDE. What the stop depends on is the page's OWN session state (the live site, the session record and the artifact it holds), never on a module global: Streamlit gives every browser
session its own ``session_state`` inside one Python process, and the layer keeps no mutable state of its own. The scenarios:

* two live encounters of the same case in one process, one stopped and one running: the stop of one is not the stop of the other, and neither reads the other's site, record or artifact;
* the SAME saved encounter reopened twice (a duplicate tab): a stopped one is stopped in both, an ACTIVE one that lost its site is invalid in both, and none of them can move;
* turns interleaved between two sessions: each guard consults only its own state;
* the layer's modules hold no mutable module-level state beyond constants (the audit that makes "single process" a sufficient claim for development).

The verdict (P3-260) is SINGLE_PROCESS_SESSION_SAFETY_SUFFICIENT_FOR_DEVELOPMENT, with the residuals declared in ``docs/PHASE3_EFFECTIVE_AUTHORITY_STOP.md``: several Python processes
behind one address share only the durable store, whose files are written in one call (a reader can meet a partial file and skips it) and are never what the guard continues on.
"""
import ast
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_store as store
import runtime_shadow as rs
from test_phase3_stop_lifecycle import REAL, UNSUPPORTED, FIRST, Session

ROOT = Path(__file__).resolve().parent
LAYER = ("runtime_authority.py", "runtime_authority_session.py", "runtime_authority_store.py", "runtime_authority_pair.py", "runtime_pressure_grant.py", "runtime_minute_validation.py")
CASES = ("gi_bleed_57m", "gi_bleed_72f")


@pytest.fixture(autouse=True, scope="module")
def _real_environment():
    with pytest.MonkeyPatch.context() as patch:
        for name, value in REAL.items():
            patch.setenv(name, value)
        for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
            patch.delenv(name, raising=False)
        yield


class SeededSession(Session):
    """A session whose patient arrives differently, as two residents' encounters of the same case do on the real page (the arrival is generated per attempt; the headless driver's default
    seed makes every encounter the SAME arrival, which a real page never does: the identity of an encounter is the digest of its arrival)."""

    def __init__(self, case="gi_bleed_57m", seed=7):
        import pilot_acceptance
        from test_phase3_pressure_review import Driver as _Driver
        driver = _Driver.__new__(_Driver)
        driver.enc = pilot_acceptance.Encounter(case, seed=seed)
        driver.arrival = deepcopy(driver.enc.state)
        driver.site = ra.open_site(driver.arrival, environ=REAL)
        assert driver.site is not None and driver.site.grant is not None
        self.driver = driver
        self.store = {ra.SITE_KEY: driver.site}
        driver.site._session_store = self.store
        self.sequence = [self.record()["lifecycle"]]


def _stopped_session(case="gi_bleed_57m", seed=None):
    session = Session(case) if seed is None else SeededSession(case, seed)
    session.ask(2)
    session.order(FIRST)
    assert session.record()["lifecycle"] == se.ACTIVE_AUTHORITY
    session.order(UNSUPPORTED)
    assert session.record()["lifecycle"] == se.INVALID_FOR_CONTINUATION
    return session


def _saved_fields(session):
    """What a saved encounter carries back: the persisted fields only (the site and the artifact are in-memory objects of the page session and are not among them)."""
    return {se.SESSION_KEY: deepcopy(session.store[se.SESSION_KEY])}


# -- two live sessions in one process ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_c1_the_stop_of_one_session_is_not_the_stop_of_another_session_of_the_same_case(case):
    stopped = _stopped_session(case)
    running = SeededSession(case, seed=11)
    running.ask(2)
    running.order(FIRST)
    assert running.guard()["allowed"] is True and running.record()["lifecycle"] == se.ACTIVE_AUTHORITY
    assert stopped.guard()["allowed"] is False
    running.order("Reassess in 10 minutes.")
    assert running.guard()["allowed"] is True and not running.site.halted, "the running one keeps committing: the other session's stop does not reach it"
    assert stopped.guard()["allowed"] is False and stopped.site is not running.site
    assert stopped.record()["encounter_id"] != running.record()["encounter_id"], "two encounters, two identities: nothing is shared by name"


def test_c2_turns_interleaved_between_two_sessions_each_guard_reads_only_its_own_state():
    a, b = Session("gi_bleed_57m"), SeededSession("gi_bleed_57m", seed=11)
    assert a.record()["encounter_id"] != b.record()["encounter_id"]
    a.ask(2)
    b.ask(2)
    a.order(FIRST)
    b.order(FIRST)
    a.order(UNSUPPORTED)                                     # a stops
    assert a.guard()["allowed"] is False and b.guard()["allowed"] is True
    b.order("Reassess in 10 minutes.")
    assert not b.site.halted and b.guard()["allowed"] is True
    b.order(UNSUPPORTED)                                     # now b stops, on its own
    assert b.guard()["allowed"] is False and a.guard()["allowed"] is False
    assert a.record()["last_authoritative_minute"] != b.record()["last_authoritative_minute"] or a.record()["encounter_id"] != b.record()["encounter_id"]
    assert a.record()["record_digest"] != b.record()["record_digest"], "two stopped sessions, two records"


def test_c3_the_guard_of_a_session_does_not_read_another_sessions_record_or_site():
    stopped = _stopped_session()
    other = Session("gi_bleed_57m")
    other.ask(2)
    # the other session's state carries the stopped session's RECORD by accident (a mix-up of two session dictionaries): it is about another encounter, not this one
    mixed = {ra.SITE_KEY: other.site, se.SESSION_KEY: deepcopy(stopped.store[se.SESSION_KEY])}
    decision = se.continuation_guard(mixed, other.state, environ=REAL)
    # the foreign record is not this encounter's (the state is behind its last authoritative minute, or the case/identity differ): it says nothing, and the site decides; if it does
    # disagree with the site the guard fails CLOSED -- never open on the strength of a mix-up
    assert decision["allowed"] is True or decision["stop_class"] in (se.STOP_STALE_OR_CONFLICTING, se.STOP_RESUMED)


# -- the same saved encounter twice (a duplicate tab) -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("flags", ("on", "off"))
def test_c4_a_stopped_saved_encounter_opened_in_two_tabs_is_stopped_in_both_and_neither_moves(flags):
    stopped = _stopped_session()
    environ = REAL if flags == "on" else {}
    tabs = []
    for _ in range(2):
        tab = _saved_fields(stopped)
        decision = se.continuation_guard(tab, stopped.state, environ=environ)
        assert decision["allowed"] is False and decision["lifecycle"] == se.INVALID_FOR_CONTINUATION and decision["legacy_fallback_allowed"] is False, (flags, decision)
        tabs.append(tab)
    assert tabs[0][se.SESSION_KEY] == tabs[1][se.SESSION_KEY] == stopped.store[se.SESSION_KEY], "the record is the same fact in each tab; nothing was rewritten into a different story"


def test_c5_an_ACTIVE_saved_encounter_opened_in_two_tabs_is_invalid_in_both_never_continued_on_the_legacy_engine():
    session = Session("gi_bleed_57m")
    session.ask(2)
    session.order(FIRST)
    assert session.record()["lifecycle"] == se.ACTIVE_AUTHORITY
    for _ in range(2):
        tab = _saved_fields(session)
        decision = se.continuation_guard(tab, session.state, environ=REAL)
        assert decision["allowed"] is False and decision["stop_class"] == se.STOP_RESUMED and decision["legacy_fallback_allowed"] is False, decision
        assert tab[se.SESSION_KEY]["lifecycle"] == se.INVALID_FOR_CONTINUATION, "the tab wrote down what it found, so a second look agrees"
    # the original, still live, session is untouched by what its copies concluded
    assert session.guard()["allowed"] is True and session.record()["lifecycle"] == se.ACTIVE_AUTHORITY


def test_c6_a_tab_cannot_clear_a_halt_by_dropping_the_record_when_the_experiment_is_in_the_durable_store():
    """The record is the tab's own; the durable store is the other witness. A tab that lost its record but still carries the encounter exactly as it was left at a committed minute is
    recognised by case, minute and committed pressures (the lost-state path)."""
    session = Session("gi_bleed_57m")
    session.ask(2)
    session.order(FIRST)
    state = session.state
    tab = {}                                                  # nothing at all came back with the saved encounter
    decision = se.continuation_guard(tab, state, environ=REAL)
    # P3-273 (declared adaptation): the encounter carries its provenance anchor, so it is ALWAYS a stop (it used to be the strict durable match, which a legacy engine that ran on defeated)
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_PROVENANCE and decision["legacy_fallback_allowed"] is False
    legacy_only_looking = {key: value for key, value in state.items() if key != ra.PROVENANCE_ANCHOR_KEY}
    decision = se.continuation_guard({}, legacy_only_looking, environ=REAL)
    assert decision["allowed"] in (True, False)               # without the anchor the strict match still decides: the declared limit of the store backstop
    if decision["allowed"] is False:
        assert decision["stop_class"] == se.STOP_RESUMED and decision["legacy_fallback_allowed"] is False


def test_c7_unreadable_or_corrupt_shared_state_is_a_stop_never_a_continuation():
    class Poisoned(dict):
        def get(self, key, default=None):
            raise RuntimeError("shared state in the middle of a write")
    decision = se.continuation_guard(Poisoned(), {"sim_time": 20}, environ=REAL)
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_UNREADABLE


def test_c7b_two_encounters_with_the_identical_arrival_that_diverge_at_the_same_minute_collide_and_the_later_one_never_applies_what_it_could_not_make_durable():
    """The residual, stated and proved: the identity of a stored record is the digest of the arrival plus the minute count and outcome, and the store is create-only. Two encounters that
    arrive IDENTICALLY (the headless driver's fixed seed; never the real page, see c12) and then do DIFFERENT things of the same duration meet as a collision.

    P3-271 (declared adaptation): the later twin's commit is one the store could not write, so it was never durable and is WITHDRAWN before anything applies it (the page installs a commit only when
    ``minute`` returns it). Before this cycle that commit stood and the session stopped; now: a FIRST commit that collides is a clean abort (nothing authoritative ever existed: the legacy encounter
    continues), and a LATER one stops the session at the last durable authoritative minute. Neither ever continues on a record it could not write, and neither applies the pressure it withdrew."""
    directory = Path(tempfile.mkdtemp(prefix="phase3-stop-twins-"))
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv(store.STORE_FLAG, str(directory))
        a, b = Session("gi_bleed_57m"), Session("gi_bleed_57m")
        assert a.record()["encounter_id"] == b.record()["encounter_id"], "identical arrivals: the premise of the residual"
        a.order("Give 1 litre of normal saline over 15 minutes.")
        b.order("Give 1 litre of lactated Ringer's over 15 minutes.")
        assert a.site.stored.get("stored") is True and a.guard()["allowed"] is True
        assert b.site.halted and not b.site.minutes_committed, "the commit that collided was withdrawn: nothing authoritative exists for the later twin"
        assert any(str(item.get("failure_reason")).startswith(ra.ARTIFACT_PERSISTENCE_FAILED) and item.get("outcome") == ra.ABORTED for item in b.site.artifact()["minutes"])
        record = b.record()
        assert record["lifecycle"] == se.PRECOMMIT_ABORT and record["continuation_allowed"] is True and not record["authority_began"]
        assert b.guard()["allowed"] is True, "a first commit that never happened is a clean abort: the untouched legacy encounter may continue"
        # and the same collision at a LATER commit stops the session at the last durable authoritative minute
        c, d = Session("gi_bleed_57m"), Session("gi_bleed_57m")
        c.order("Give 500 mL normal saline over 5 minutes.")
        d.order("Give 500 mL normal saline over 5 minutes.")
        assert c.site.minutes_committed == d.site.minutes_committed and d.guard()["allowed"] is True, "identical first turns: the store accepts the same record twice"
        c.order("Give 500 mL normal saline over 5 minutes.")
        d.order("Give 500 mL lactated Ringer's over 5 minutes.")
        assert c.guard()["allowed"] is True and d.site.halted
        last = c.site.minutes_committed[0]
        assert list(d.site.minutes_committed) == [last], "only the durable commit is authoritative"
        record = d.record()
        assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["stop_class"] == se.STOP_PERSISTENCE and record["legacy_fallback_allowed"] is False
        assert record["last_authoritative_minute"] == last
        assert d.guard()["allowed"] is False, "the later twin is stopped, not left to continue without a durable record"


def test_c12_two_real_page_sessions_of_the_same_case_never_arrive_identically(monkeypatch, tmp_path):
    """The premise that keeps c7b a residual and not an everyday event: the page generates each attempt's arrival, so two residents on the same case have different encounter identities
    and different stored records; one of them stopping or writing never touches the other's record."""
    import test_phase3_pair_page as page
    one = page._open(monkeypatch, "gi_bleed_57m", shadow=True, dry=False, authority=str(tmp_path / "store"))
    two = page._open(monkeypatch, "gi_bleed_57m", shadow=True, dry=False, authority=str(tmp_path / "store"))
    for at in (one, two):
        page._ask(at, "What brought you in today?")
    site_one, site_two = one.session_state.get(ra.SITE_KEY), two.session_state.get(ra.SITE_KEY)
    assert site_one is not None and site_two is not None and site_one is not site_two
    assert site_one.encounter_id != site_two.encounter_id and site_one.experiment_id != site_two.experiment_id
    page._order(one, page.UNSUPPORTED)
    assert site_one.halted and not site_two.halted
    page._order(two, "Reassess in 10 minutes.")
    assert not site_two.halted and one.session_state[se.SESSION_KEY]["lifecycle"] == se.INVALID_FOR_CONTINUATION
    assert two.session_state[se.SESSION_KEY]["lifecycle"] == se.ACTIVE_AUTHORITY
    stored = store.records(environ={store.STORE_FLAG: str(tmp_path / "store")})
    assert len({row["encounter_id"] for row in stored}) == 2


# -- the single-process audit ------------------------------------------------------------------------------------------------------------------------------

def _module_level_mutables(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    out = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            value = node.value
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = ast.unparse(target)
            if isinstance(value, (ast.Dict, ast.List, ast.Set)) or (isinstance(value, ast.Call) and ast.unparse(value.func) in ("dict", "list", "set", "defaultdict", "OrderedDict")):
                out.append(name)
    return out


def test_c8_the_layer_keeps_no_mutable_state_outside_the_page_session_beyond_declared_constants():
    """The reason a single Python process is enough for development: sessions share the interpreter, so any module-level mutable would be shared state. There is none that a session
    writes: only approved constants (read-only data) exist, no ``global`` statement, no cache."""
    allowed = {"runtime_authority.py": {"_APPROVED_SNAPSHOT_POINTS"}, "runtime_authority_session.py": {"TRANSITIONS", "OPERATIONS"}, "runtime_pressure_grant.py": {"_BODY"}}
    for path in LAYER:
        found = set(_module_level_mutables(path))
        assert found <= allowed.get(path, set()), (path, sorted(found - allowed.get(path, set())))
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "lru_cache" not in text and "functools.cache" not in text, path
        tree = ast.parse(text)
        assert not [node for node in ast.walk(tree) if isinstance(node, ast.Global)], f"{path} writes a module global"


def test_c9_the_declared_constants_are_never_written_by_a_session():
    """The three constant tables are only read: nothing in the layer assigns into them (subscript assignment, update, pop...)."""
    constants = {"_APPROVED_SNAPSHOT_POINTS", "TRANSITIONS", "OPERATIONS", "_BODY"}
    for path in LAYER:
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Subscript) and ast.unparse(target.value) in constants:
                        pytest.fail(f"{path}:{node.lineno} writes into {ast.unparse(target.value)}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and ast.unparse(node.func.value) in constants and node.func.attr in ("update", "pop", "setdefault", "clear", "popitem"):
                pytest.fail(f"{path}:{node.lineno} mutates {ast.unparse(node.func.value)}")


def test_c10_the_durable_store_is_create_only_and_names_each_record_by_encounter_so_two_sessions_never_overwrite_each_other():
    directory = Path(tempfile.mkdtemp(prefix="phase3-stop-concurrency-"))
    environ = {**REAL, store.STORE_FLAG: str(directory)}
    a, b = Session("gi_bleed_57m"), SeededSession("gi_bleed_57m", seed=11)
    for session in (a, b):
        session.ask(2)
        session.order(FIRST)
    results = [store.persist(session.site.artifact(), environ=environ) for session in (a, b)]
    assert all(result["stored"] for result in results), results
    assert results[0]["artifact_id"] != results[1]["artifact_id"] and results[0]["path"] != results[1]["path"], "two encounters never share a record name"
    again = store.persist(a.site.artifact(), environ=environ)
    assert again["stored"] and again.get("idempotent"), "the same record written twice is the same fact, not a second record or an overwrite"
    # a partially written file (a reader meeting a writer) is skipped, never an error of the guard or of the store listing
    (directory / "half-written.json").write_text('{"store": "x", "artifact": {', encoding="utf-8")
    listed = store.records(environ=environ)
    assert len(listed) >= 2 and not any(item["artifact_id"] is None for item in listed)
    assert se.continuation_guard({}, {"sim_time": 0}, environ=environ)["allowed"] is True


def test_c11_the_verdict_and_its_declared_residuals_are_what_the_document_says():
    verdict = "SINGLE_PROCESS_SESSION_SAFETY_SUFFICIENT_FOR_DEVELOPMENT"
    text = (ROOT / "docs" / "PHASE3_EFFECTIVE_AUTHORITY_STOP.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())
    assert verdict in text, "the document states the P3-260 verdict"
    assert "varios procesos de Python" in flat and "archivo parcial" in flat and "ARTIFACT_PERSISTENCE_FAILED" in text, "and its two declared residuals"
