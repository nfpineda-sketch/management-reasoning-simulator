"""P3-269 to P3-271: the authority-controlled TURN (``runtime_authority_turn``) -- its ownership table, its verdict and its copy/apply/discard mechanics.

TEST-SIDE, with a stub site and a plain dictionary for the page's session store: nothing here runs the engine or the page (the page, the failure matrix and the recovery are in
``test_phase3_turn_page`` and ``test_phase3_provenance_anchor``). What is proved:

* every saved session field of the encounter has exactly ONE ownership class, so a new field cannot be added without deciding whether a turn copies it;
* a transaction exists only for a REAL session (a grant) that has ALREADY committed and is not halted: with no site, a site without a grant, a halted site or a site that has not committed it is one
  dictionary lookup and the ordinary page;
* the working copy is a deep copy; the ORIGINAL objects are never touched; a discard puts back the very same objects (identity, not equal values) and removes what the turn created;
* the AI spend, the submission journal and the authority's own record are never copied and never restored;
* the verdict is read from the site's facts and fails closed.
"""
from copy import deepcopy

import pytest

import runtime_authority as ra
import runtime_authority_turn as tu
from curriculum_runtime import SESSION_FIELDS


class StubSite:
    """The facts of an authority site the turn reads, and nothing else."""

    def __init__(self, *, grant=True, halted=False, committed=(2,)):
        self.grant = {"grant_id": "stub"} if grant else None
        self.halted = halted
        self.records = [{"minute": minute, "committed": ["sbp", "dbp"]} for minute in committed]
        self.no_advance_turns = []
        self.unjudged = []

    def halt_unjudged_turn(self, minute, detail):
        """What the real site does when a turn moved the clock and was never shown to it: it stops (and says why)."""
        self.unjudged.append((minute, detail))
        self.halted = True

    @property
    def minutes_committed(self):
        return tuple(record["minute"] for record in self.records if record["committed"])

    def commit(self, minute):
        self.records.append({"minute": minute, "committed": ["sbp", "dbp"]})


def _store(site=None, **fields):
    store = {"state": {"sim_time": 7, "observable": {"sbp": 80}}, "events": [{"kind": "you", "text": "hi"}], "history": [], "management_trace": [], "order_ledger": [],
             "last_parse": None, "rng_counter": 3, "pending_action": None, "pending_bundle": None, "pending_reasoning": None, "reasoning_gate_counter": 1,
             "last_executed_action": None, "submission_log": [{"id": "s1", "status": "processing"}], "ai_call_ledger": [], "ai_calls_spent": 0, "phase3_authority_session": {"lifecycle": "ACTIVE_AUTHORITY"}}
    store.update(fields)
    if site is not None:
        store[ra.SITE_KEY] = site
    return store


# -- the ownership table -------------------------------------------------------------------------------------------------------------------------------------

def test_u1_every_saved_session_field_has_exactly_one_turn_ownership_class():
    assert tu.ownership_problems(SESSION_FIELDS) == []
    classified = [field for fields in tu.OWNERSHIP.values() for field in fields]
    assert sorted(classified) == sorted(SESSION_FIELDS), "the table is a partition of the saved fields, nothing more and nothing less"


def test_u1b_the_partition_check_fails_on_an_unclassified_a_doubly_classified_and_a_phantom_field(monkeypatch):
    assert any("new_saved_field" in problem and "no turn ownership class" in problem for problem in tu.ownership_problems(tuple(SESSION_FIELDS) + ("new_saved_field",)))
    monkeypatch.setitem(tu.OWNERSHIP, "OPERATIONAL", tu.OPERATIONAL + ("state",))
    assert any("state is in both" in problem for problem in tu.ownership_problems(SESSION_FIELDS))
    monkeypatch.setitem(tu.OWNERSHIP, "OPERATIONAL", tu.OPERATIONAL + ("a_phantom",))
    assert any("a_phantom is classified but is not a saved session field" in problem for problem in tu.ownership_problems(SESSION_FIELDS))


def test_u1c_what_a_turn_copies_and_what_it_must_never_restore():
    assert {"state", "events", "management_trace", "order_ledger", "history", "pending_reasoning"} <= set(tu.TURN_OWNED)
    assert not {"ai_call_ledger", "ai_calls_spent", "submission_log", "phase3_authority_session"} & set(tu.TURN_OWNED), "paid calls, the submission journal and the authority's own record are never copied"
    assert set(tu.EXTERNAL_ACCOUNTING) == {"ai_call_ledger", "ai_calls_spent"}


# -- when a turn is transactional ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("label,store", [
    ("no site (every flag off, the first pilot, a legacy encounter)", _store()),
    ("a site without a grant (a test-only point)", _store(StubSite(grant=False))),
    ("a halted site", _store(StubSite(halted=True))),
    ("a site that has not committed yet (the clean-abort case)", _store(StubSite(committed=()))),
])
def test_u2_there_is_no_transaction_unless_a_real_session_has_committed_and_can_continue(label, store):
    assert tu.begin(store) is tu.NO_TURN, label
    assert tu.applies(store) is False
    with tu.begin(store) as turn:
        store["state"]["sim_time"] = 99                      # the ordinary page: the turn runs on the real objects, exactly as before
    assert store["state"]["sim_time"] == 99 and tu.TURN_KEY not in store and turn.verdict() == tu.COMMIT


def test_u2b_a_real_committed_session_gets_a_transactional_turn_and_a_turn_inside_a_turn_is_the_outers():
    store = _store(StubSite())
    turn = tu.begin(store, route="order_turn")
    assert isinstance(turn, tu.AuthorityTurn) and tu.applies(store)
    with turn:
        assert tu.begin(store) is tu.NO_TURN, "a nested turn is the outer turn's"
        assert store[tu.TURN_KEY] is turn


# -- the copy, the commit and the discard -------------------------------------------------------------------------------------------------------------------

def test_u3_the_working_copy_is_a_deep_copy_and_the_originals_are_never_touched():
    site = StubSite()
    store = _store(site)
    originals = {key: store[key] for key in tu.TURN_OWNED}
    snapshot = deepcopy(originals)
    with tu.begin(store) as turn:
        for key in tu.TURN_OWNED:
            assert store[key] == originals[key] and (store[key] is not originals[key] or originals[key] is None or isinstance(originals[key], (int, str))), key
        store["state"]["sim_time"] = 99
        store["state"]["observable"]["sbp"] = 1
        store["events"].append({"kind": "x"})
        store["order_ledger"].append({"order_id": "t:0", "fate": "EXECUTED"})
        store["management_trace"].append({"activity_kind": "x"})
        site.halted = True                                   # the authority halts during the turn
    assert turn.decided == tu.DISCARD
    assert originals == snapshot, "the original objects were never mutated by the turn"


def test_u4_a_valid_turn_keeps_the_validated_copy_as_the_real_encounter_and_clears_its_mark():
    site = StubSite()
    store = _store(site)
    original_state = store["state"]
    with tu.begin(store) as turn:
        store["state"]["sim_time"] = 12
        site.commit(12)                                      # a durable commit this turn
    assert turn.decided == tu.COMMIT
    assert store["state"]["sim_time"] == 12 and store["state"] is not original_state and original_state["sim_time"] == 7
    assert tu.TURN_KEY not in store


def test_u5_a_discard_puts_back_the_very_same_objects_and_removes_what_the_turn_created():
    site = StubSite()
    store = _store(site)
    del store["last_executed_action"]                        # a key the encounter did not have before this turn
    identities = {key: id(store[key]) for key in tu.TURN_OWNED if key in store}
    with tu.begin(store) as turn:
        store["last_executed_action"] = {"created": "by the turn"}
        store["state"]["sim_time"] = 99
        site.halted = True
    assert turn.decided == tu.DISCARD
    assert {key: id(store[key]) for key in tu.TURN_OWNED if key in store} == identities, "identity, not equal values: nothing was restored from a copy"
    assert "last_executed_action" not in store and store["state"]["sim_time"] == 7
    assert tu.TURN_KEY not in store


def test_u6_what_a_turn_must_never_restore_survives_a_discard():
    site = StubSite()
    store = _store(site)
    ledger, spent, journal, record = store["ai_call_ledger"], store["ai_calls_spent"], store["submission_log"], store["phase3_authority_session"]
    with tu.begin(store):
        store["ai_call_ledger"].append({"call": "paid"})     # a paid call that DID happen
        store["ai_calls_spent"] = 4
        store["submission_log"][0]["status"] = "blocked_by_authority_failure"
        store["phase3_authority_session"] = {"lifecycle": "INVALID_FOR_CONTINUATION"}
        site.halted = True
    assert store["ai_call_ledger"] is ledger and ledger == [{"call": "paid"}], "restoring the AI ledger would hide a cost that was real"
    assert store["ai_calls_spent"] == 4
    assert store["submission_log"] is journal and journal[0]["status"] == "blocked_by_authority_failure"
    assert store["phase3_authority_session"]["lifecycle"] == "INVALID_FOR_CONTINUATION", "the authority's rejection stays"
    assert record != store["phase3_authority_session"]


# -- the verdict ----------------------------------------------------------------------------------------------------------------------------------------------

def _verdict_after(change, *, committed=(2,)):
    site = StubSite(committed=committed)
    store = _store(site)
    turn = tu.begin(store)
    with turn:
        change(site, store)
        verdict = turn.verdict()
    return verdict


def test_u7_the_verdict_is_read_from_the_sites_own_facts_and_fails_closed():
    assert _verdict_after(lambda site, store: None) == tu.COMMIT, "a turn the authority did not refuse (a quiet or valid turn)"
    assert _verdict_after(lambda site, store: site.commit(9)) == tu.COMMIT, "a durable commit: the encounter reached that minute"
    assert _verdict_after(lambda site, store: setattr(site, "halted", True)) == tu.DISCARD, "halted during the turn with no commit: refused"
    assert _verdict_after(lambda site, store: (site.commit(9), setattr(site, "halted", True))) == tu.COMMIT, "commit, then halt (a later persist): the commit is real and the NEXT operation stops"
    assert _verdict_after(lambda site, store: store.__setitem__(ra.SITE_KEY, None)) == tu.DISCARD, "the site that began the turn is gone: nobody judged it"
    assert _verdict_after(lambda site, store: store.__setitem__(ra.SITE_KEY, StubSite())) == tu.DISCARD, "a different site is not the one that began the turn"
    assert _verdict_after(lambda site, store: site.records.pop()) == tu.DISCARD, "a commit that was withdrawn is never applied"


def test_u7c_a_turn_that_moved_the_clock_and_that_the_site_never_judged_is_not_applied_and_stops_the_session():
    """P3-276, review H1: the site records NOTHING for a turn it was never shown, and an unchanged site used to read as 'the authority did not refuse'. A working copy whose clock moved with
    nothing recorded -- no minute, no quiet turn, no refusal -- was never judged, so it is not applied and the session stops."""
    def moved(site, store):
        store["state"]["sim_time"] = 9                           # the legacy engine let two minutes pass on the copy
    site = StubSite()
    store = _store(site)
    reached = []
    with tu.begin(store) as turn:
        moved(site, store)
        tu.check(store)
        reached.append("never")
    assert reached == [] and turn.decided == tu.DISCARD and store["state"]["sim_time"] == 7, "the clock the real encounter had is the clock it keeps"
    assert site.unjudged and site.unjudged[0][0] == 9 and "never judged" in site.unjudged[0][1] and site.halted, "and the session is stopped, with the reason"
    assert "TURN_NOT_JUDGED" in str(ra.TURN_NOT_JUDGED) or ra.TURN_NOT_JUDGED.startswith("AUTHORITY_TURN_NOT_JUDGED")


def test_u7d_the_same_turn_is_a_commit_when_the_site_recorded_anything_for_it():
    """What the site recorded (a minute, a quiet turn, a refusal) is what proves it judged the turn: the clock moving is then ordinary."""
    assert _verdict_after(lambda site, store: (store["state"].__setitem__("sim_time", 9), site.records.append({"minute": 9, "committed": []}))) == tu.COMMIT, "a recorded refusal that did not halt"
    assert _verdict_after(lambda site, store: (store["state"].__setitem__("sim_time", 9), site.no_advance_turns.append({"minute": 9}))) == tu.COMMIT, "a recorded zero-minute turn"
    assert _verdict_after(lambda site, store: (store["state"].__setitem__("sim_time", 9), site.commit(9))) == tu.COMMIT, "a durable commit"
    assert _verdict_after(lambda site, store: store["state"].__setitem__("observable", {"sbp": 70})) == tu.COMMIT, "a turn that moved no clock has nothing the authority had to judge"


def test_u7e_an_exit_through_an_exception_discards_the_unjudged_turn_without_stopping_the_session():
    """The interrupted turn changes nothing (its working copy is dropped) and an interruption is not a failure of the authority, so the session is not stopped for it."""
    site = StubSite()
    store = _store(site)
    with pytest.raises(RuntimeError):
        with tu.begin(store):
            store["state"]["sim_time"] = 9
            raise RuntimeError("the page run was interrupted")
    assert store["state"]["sim_time"] == 7 and not site.halted and site.unjudged == []
    assert tu.TURN_KEY not in store


def test_u7f_a_turn_that_ends_normally_with_an_unjudged_clock_move_is_discarded_and_stops_the_session():
    """The page forgot to call ``check`` (or a route is not wired): the exit applies the same verdict and the same stop, so a forgotten check is not a silent legacy minute."""
    site = StubSite()
    store = _store(site)
    with tu.begin(store):
        store["state"]["sim_time"] = 9
    assert store["state"]["sim_time"] == 7 and site.halted and site.unjudged


def test_u7b_a_verdict_that_cannot_be_read_is_a_discard():
    site = StubSite()
    store = _store(site)
    turn = tu.begin(store)
    with turn:
        class Broken:
            @property
            def halted(self):
                raise RuntimeError("boom")
        store[ra.SITE_KEY] = Broken()
        assert turn.verdict() == tu.DISCARD


# -- a turn an earlier run left open (P3-276, review L2) ---------------------------------------------------------------------------------------------------------

def test_u11_a_turn_left_open_by_an_earlier_run_is_closed_with_its_own_verdict_at_the_start_of_the_next_run():
    site = StubSite()
    store = _store(site)
    turn = tu.begin(store)
    turn.__enter__()                                                  # the page run died here: the context was never closed
    store["state"]["sim_time"] = 9                                    # and the copy had moved the clock, unjudged
    assert tu.begin(store) is tu.NO_TURN, "while the stale turn is open every later turn would be 'a turn inside a turn' and run untransacted"
    assert tu.reset_stale(store) == tu.DISCARD and store["state"]["sim_time"] == 7 and tu.TURN_KEY not in store, "the stale turn is closed: the original encounter is back"
    assert isinstance(tu.begin(store), tu.AuthorityTurn), "and the next turn is transactional again"
    assert tu.reset_stale(store) is None, "nothing open: one lookup, no decision"


def test_u11b_a_stale_turn_that_the_authority_held_valid_stays_applied_and_anything_unreadable_is_discarded():
    site = StubSite()
    store = _store(site)
    turn = tu.begin(store)
    turn.__enter__()
    store["state"]["sim_time"] = 9
    site.commit(9)
    assert tu.reset_stale(store) == tu.COMMIT and store["state"]["sim_time"] == 9 and tu.TURN_KEY not in store
    store[tu.TURN_KEY] = object()                                     # not a turn of this layer
    assert tu.reset_stale(store) == tu.DISCARD and tu.TURN_KEY not in store


# -- unwinding and exits ---------------------------------------------------------------------------------------------------------------------------------------

def test_u8_check_unwinds_a_refused_turn_and_the_context_swallows_only_that_unwinding():
    site = StubSite()
    store = _store(site)
    reached = []
    with tu.begin(store) as turn:
        store["state"]["sim_time"] = 99
        site.halted = True
        tu.check(store)                                      # raises AuthorityTurnDiscarded, swallowed by the context
        reached.append("never: the statements after the verdict (the trace, the final save) must not run")
    assert reached == [] and turn.decided == tu.DISCARD and store["state"]["sim_time"] == 7


def test_u8b_check_does_nothing_for_a_valid_turn_or_when_no_turn_is_open():
    tu.check({})                                             # no turn: one lookup
    site = StubSite()
    store = _store(site)
    with tu.begin(store) as turn:
        tu.check(store)
        store["state"]["sim_time"] = 12
        site.commit(12)
        tu.check(store)
    assert turn.decided == tu.COMMIT and store["state"]["sim_time"] == 12


def test_u9_any_other_exit_applies_the_verdict_and_lets_the_exception_keep_going():
    # a rerun (or an error) after the authority refused: the encounter must still be the original
    site = StubSite()
    store = _store(site)
    with pytest.raises(RuntimeError):
        with tu.begin(store) as turn:
            store["state"]["sim_time"] = 99
            site.halted = True
            raise RuntimeError("a rerun that arrives after the refusal")
    assert turn.decided == tu.DISCARD and store["state"]["sim_time"] == 7 and tu.TURN_KEY not in store
    # and a rerun in a turn the authority held valid keeps the work done so far, exactly as the page always did
    site = StubSite()
    store = _store(site)
    with pytest.raises(RuntimeError):
        with tu.begin(store) as turn:
            store["state"]["sim_time"] = 12
            site.commit(12)                                  # P3-276: the authority judged it (a durable commit) before the rerun; an unjudged clock move is discarded (u7c)
            raise RuntimeError("a rerun")
    assert turn.decided == tu.COMMIT and store["state"]["sim_time"] == 12


def test_u10_the_cheap_path_is_one_lookup_when_nothing_is_open_and_the_layer_reaches_no_engine_or_page():
    class Counting(dict):
        reads = 0

        def get(self, key, default=None):
            Counting.reads += 1
            return super().get(key, default)
    store = Counting({"state": {}})
    assert tu.begin(store) is tu.NO_TURN
    assert Counting.reads == 1, "no site: one lookup"
    import ast
    from pathlib import Path
    tree = ast.parse((Path(__file__).resolve().parent / "runtime_authority_turn.py").read_text(encoding="utf-8"))
    imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert imported <= {"__future__", "copy", "typing", "runtime_authority"}, imported
