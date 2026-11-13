"""P3-271 to P3-275: the authority-controlled TURN on the REAL page (Streamlit ``AppTest``), both GI cases: the failed turn never happened to the real encounter.

TEST-SIDE. The authorized development configuration (the real approved pressure snapshot, the real grant, an artifact store) is played through the page itself. After the first REAL authority commit, a
turn the authority refuses used to have run on the real encounter first (R-FAILOPEN-1: the clock, the patient, the ledger, the events and the Management Trace had already moved, and the stop began at the NEXT
operation). The turn now runs on working copies and the originals stay the encounter. For every refusal in the matrix, on the order route AND on the clock route:

* the encounter -- patient state (with its clock), events, history, Management Trace, order ledger, parse, pending holds, counters -- is IDENTICAL to what it was right before the turn that executes;
* the real clock did not move, the provenance anchor is unchanged, and no authority minute was committed (the artifact names the refused minute as ABORTED);
* the session is INVALID_FOR_CONTINUATION and the next operation is blocked (the stop of P3-250 to P3-264 is unchanged, and now it holds from the very turn that failed);
* nothing was claimed as executed: the ledger has no row for the refused order.

Before the first commit a refusal is a clean abort and the legacy turn stands (FD-STOP-04). With every flag off nothing changes.
"""
import json
from copy import deepcopy

import pytest

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_store as store
import runtime_authority_turn as tu
import runtime_minute_validation as validation
import runtime_pressure_grant as grants
import test_phase3_pair_page as page
import test_phase3_stop_page as stop
from curriculum_runtime import SESSION_FIELDS

CASES = page.CASES
ORDER = "Give 500 mL normal saline over 5 minutes."


def _encounter(at):
    """Everything a turn owns, as the resident's record sees it, in one canonical string."""
    return json.dumps({key: at.session_state[key] for key in tu.TURN_OWNED if key in at.session_state}, sort_keys=True, default=str)


class Snapshot(str):
    """The encounter as it stood right before the executing turn, and whether that turn was a guided release of a held order (which has no journal entry of its own)."""
    gated = False


def _execute(at, text):
    """One order as a resident gives it. Returns the encounter exactly as it stood right before the turn that EXECUTES it: the reasoning gate's hold is its own legitimate zero-minute turn (the order is held,
    nothing runs), so when the page holds the order the snapshot is taken after the hold and before the guided completion that releases it."""
    page._mode(at, "Treat")
    next(item for item in at.text_area if item.label == "Enter your clinical reasoning and/or actions").set_value(text)
    before = Snapshot(_encounter(at))
    next(button for button in at.button if button.label == "Send").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    if at.session_state["pending_reasoning"]:
        before = Snapshot(_encounter(at))
        before.gated = True
        for label, answer in zip(page.FOUR_FIELDS, page.ANSWERS):
            if answer is not None:
                next(item for item in at.text_area if item.label == label).set_value(answer)
        next(button for button in at.button if button.label == "Complete reasoning & execute held order").click().run()
        assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return before


def _anchor(at):
    return dict(at.session_state["state"].get(ra.PROVENANCE_ANCHOR_KEY) or {})


def _two_commits(monkeypatch, tmp_path, case):
    at = stop._open(monkeypatch, tmp_path, case)
    site = stop._first_commit(at)
    page._order(at, ORDER)
    assert not site.halted and len(site.minutes_committed) == 2, (site.halt_reason, site.minutes_committed)
    return at, site


def _no_turn_left_open(at):
    assert tu.TURN_KEY not in at.session_state, "a turn is never open between two page runs"


def _refused_turn_proofs(at, site, *, before, minute, committed, last, anchor):
    """The proofs shared by every refusal: the encounter did not move, nothing was committed, nothing is claimed, the session stopped."""
    assert site.halted, site.halt_reason
    assert _encounter(at) == before, "the refused turn left the real encounter exactly as it was right before it"
    assert page._minute(at) == minute, "the real clock did not move"
    assert list(site.minutes_committed) == committed, "no authority minute was committed"
    assert _anchor(at) == anchor and anchor["last_authority_minute"] == last, "the provenance anchor is unchanged"
    _no_turn_left_open(at)


# -- a valid turn becomes the real encounter ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_t1_a_valid_authoritative_turn_is_the_real_turn_and_carries_its_provenance(monkeypatch, tmp_path, case):
    at, site = _two_commits(monkeypatch, tmp_path, case)
    _no_turn_left_open(at)
    committed = list(site.minutes_committed)
    state = at.session_state["state"]
    anchor = _anchor(at)
    record = stop._record(at)
    assert record["lifecycle"] == se.ACTIVE_AUTHORITY and record["last_authoritative_minute"] == committed[-1] == page._minute(at)
    assert (anchor["first_authority_minute"], anchor["last_authority_minute"], anchor["commits"]) == (committed[0], committed[-1], len(committed))
    assert se.anchor_problems(anchor) == [] and anchor["grant_id"] == record["grant_id"] and anchor["encounter_id"] == record["encounter_id"]
    observable = state["observable"]
    pressure = record["last_authoritative_pressure"]
    assert (observable["sbp"], observable["dbp"]) == (pressure["sbp"], pressure["dbp"]), "the validated copy IS the encounter: it carries the pressures the authority committed"
    assert ra.PROVENANCE_ANCHOR_KEY not in observable, "the anchor is metadata outside the observable and outside the authority domain"
    assert se.continuation_guard(at.session_state, state)["allowed"] is True


# -- P3-272: the order route, every refusal --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,inject,order,reason,stop_class", stop.MATRIX, ids=[row[0] for row in stop.MATRIX])
def test_t2_a_refused_order_turn_never_happened_to_the_real_encounter(monkeypatch, tmp_path, name, inject, order, reason, stop_class):
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    if inject is not None:
        inject(monkeypatch)
    before = _execute(at, order)
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    # P3-276 (review L3): the ledger is compared with the snapshot taken right before the refused turn, as a number and not through an escape clause
    assert len(at.session_state["order_ledger"]) == len(json.loads(before.replace("NaN", "null"))["order_ledger"]), "the refused turn added no row to the order ledger"
    record = stop._record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["halt_reason"].startswith(reason), (name, record["halt_reason"])
    assert record["stop_class"] == stop_class and record["continuation_allowed"] is False and record["legacy_fallback_allowed"] is False
    assert record["last_authoritative_minute"] == last, "the last authoritative state is the real encounter's own state"
    assert record["failed_minute"] is not None and record["failed_operation"], "the refused minute is named: it is a record of what was refused, not of what happened"
    assert site.is_for(at.session_state["state"]), "the halted site is still THIS encounter's site: the real clock legitimately stays behind the refused minute"
    if not before.gated:
        entry = (at.session_state.get("submission_log") or [])[-1]
        assert entry["status"] == "blocked_by_authority_failure", ("the refused submission is marked blocked in the journal, not 'processed'", entry["status"])
    refused = [item for item in site.artifact()["minutes"] if item.get("outcome") == ra.ABORTED]
    assert refused, "the artifact names the refused turn as ABORTED"
    assert not [item for item in site.artifact()["minutes"] if item.get("committed") and ra._as_int(item.get("minute")) > last], "and no minute past the last authoritative one is committed"
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", (grants.GRANT,))          # undo the injection so only the STOP blocks what follows
    stop._assert_stopped(at, last_authoritative=last, stop_class=stop_class)
    stop._blocked_attempts(at, monkeypatch)


def test_t2b_a_persistence_failure_withdraws_the_commit_that_was_never_durable_and_never_applied(monkeypatch, tmp_path):
    """R-FAILOPEN-1, the one commit that could be taken back: it existed only in memory for the length of ``minute`` (the store could not write it), so it is withdrawn and recorded as the refused minute."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, minute = list(site.minutes_committed), page._minute(at)
    stop._inject_persistence(monkeypatch)
    before = _execute(at, "Reassess in 10 minutes.")
    assert site.halted and _encounter(at) == before and page._minute(at) == minute and list(site.minutes_committed) == committed
    refused = [item for item in site.artifact()["minutes"] if item.get("outcome") == ra.ABORTED and str(item.get("failure_reason")).startswith(ra.ARTIFACT_PERSISTENCE_FAILED)]
    assert refused and "was not durable and was not applied" in refused[-1]["failure_reason"]
    assert refused[-1]["committed"] == [] and "common_pressures" not in refused[-1] and "moved_fields" not in refused[-1]
    assert stop._record(at)["stop_class"] == se.STOP_PERSISTENCE and stop._record(at)["last_authoritative_minute"] == committed[-1]


def test_t11_a_commit_that_was_durable_is_never_withdrawn_when_a_later_write_of_the_same_turn_fails(monkeypatch, tmp_path):
    """The withdrawal is only for the commit the store could NOT write. A commit that was durable (the artifact is on disk) is a fact the encounter reached: if the turn's LATER write (the provenance
    settlement) fails, the experiment stops from the next operation and the turn stays applied: the artifact on disk and the encounter agree."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, minute = list(site.minutes_committed), page._minute(at)
    real, calls = store.persist, {"n": 0}

    def flaky(artifact, environ=None):
        calls["n"] += 1
        return real(artifact, environ=environ) if calls["n"] == 1 else {"stored": False, "why": "STORE_ERROR OSError: disk full"}
    monkeypatch.setattr(store, "persist", flaky)
    _execute(at, ORDER)
    assert calls["n"] >= 2, "the premise: the commit's own write succeeded and a later write of the turn failed"
    assert site.halted and site.halt_reason.startswith(ra.ARTIFACT_PERSISTENCE_FAILED)
    assert len(site.minutes_committed) == len(committed) + 1, "the durable commit stands: it is never taken back"
    assert page._minute(at) == max(site.minutes_committed) > minute, "and the turn it belongs to was applied"
    record = stop._record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["last_authoritative_minute"] == max(site.minutes_committed)
    assert _anchor(at)["last_authority_minute"] == max(site.minutes_committed)
    _no_turn_left_open(at)


@pytest.mark.parametrize("failing_offset", (1, 59))
def test_t12_a_failure_inside_a_long_interval_aborts_the_whole_turn_and_none_of_its_minutes_reach_the_real_encounter(monkeypatch, tmp_path, failing_offset):
    """The turn commits the engine's END state, so EVERY internal minute of a 60-minute infusion is validated; the first failing minute refuses all of it. The real encounter is at the minute it was
    at: not one of the sixty happened to it (the interval is atomic for the encounter as it already was for the record)."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    target = minute + failing_offset
    original = validation.pressure_failures
    monkeypatch.setattr(validation, "pressure_failures", lambda m, **kwargs: list(original(m, **kwargs)) + (["injected_internal_minute_failure"] if m == target else []))
    before = _execute(at, "Give 1 litre of normal saline over 60 minutes. Reassess in 60 minutes.")
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    failed = next(record for record in site.records if record["outcome"] == ra.ABORTED)
    assert failed["interval_validation"]["first_failed_minute"] == target, failed["interval_validation"]
    assert stop._record(at)["last_authoritative_minute"] == last and stop._record(at)["stop_class"] == se.STOP_VALIDATION


# -- the clock route: a question, a topic, an examination ----------------------------------------------------------------------------------------------

CLOCK_ROWS = tuple(row for row in stop.MATRIX if row[0] in ("validation_failure", "internal_error", "wrong_grant", "artifact_persistence", "replay_mismatch"))


@pytest.mark.parametrize("ask", ("question", "examination"))
@pytest.mark.parametrize("name,inject,order,reason,stop_class", CLOCK_ROWS, ids=[row[0] for row in CLOCK_ROWS])
def test_t3_a_refused_clock_turn_leaves_no_question_no_answer_no_examination_and_no_minute(monkeypatch, tmp_path, ask, name, inject, order, reason, stop_class):
    at, site = _two_commits(monkeypatch, tmp_path, CASES[1])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    events_before, trace_before = len(at.session_state["events"]), len(at.session_state["management_trace"])
    inject(monkeypatch)
    before = _encounter(at)
    (page._ask(at, "Where does it hurt?") if ask == "question" else page._examine(at))
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert len(at.session_state["events"]) == events_before and len(at.session_state["management_trace"]) == trace_before, "no 'you' line, no answer, no finding and no trace entry"
    record = stop._record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["stop_class"] == stop_class and record["last_authoritative_minute"] == last
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", (grants.GRANT,))
    stop._assert_stopped(at, last_authoritative=last, stop_class=stop_class)
    stop._blocked_attempts(at, monkeypatch)


# -- the collapse boundary ------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_t4_the_turn_that_would_cross_the_collapse_boundary_is_never_applied_to_the_real_encounter(monkeypatch, tmp_path, case):
    at = stop._open(monkeypatch, tmp_path, case)
    for _ in range(3):
        page._order(at, "Reassess in 60 minutes.")
    site = stop._site(at)
    assert max(site.minutes_committed) == 180 and not site.halted
    observable_before = deepcopy(at.session_state["state"]["observable"])
    committed, anchor = list(site.minutes_committed), _anchor(at)
    before = _execute(at, "Reassess in 60 minutes.")                         # minutes 181..240: ESTABLISHED collapse from 207
    _refused_turn_proofs(at, site, before=before, minute=180, committed=committed, last=180, anchor=anchor)
    assert site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_REACHED)
    record = stop._record(at)
    assert record["failed_minute"] == 240 and record["last_authoritative_minute"] == 180 and record["stop_class"] == se.STOP_COLLAPSE_BOUNDARY
    assert at.session_state["state"]["observable"] == observable_before, "the real patient is at minute 180: the boundary-crossing interval did not happen to it (no terminal state, no common word)"
    stop._assert_stopped(at, last_authoritative=180, stop_class=se.STOP_COLLAPSE_BOUNDARY, reason_prefix=ra.COLLAPSE_BOUNDARY_REACHED)


# -- P3-272A: zero-minute mutating actions and held orders -----------------------------------------------------------------------------------------------------

def test_t5_a_zero_minute_mutating_order_cannot_bypass_the_transactional_judgement(monkeypatch, tmp_path):
    """'Order urgent endoscopy.' moves no minute: it used to be executed by the legacy engine and refused afterwards. The turn is refused BEFORE it exists in the real encounter."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    before = _execute(at, "Order urgent endoscopy.")
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert site.halt_reason.startswith(ra.MINUTE_ALREADY_COMMITTED)
    assert "endoscopy" not in json.dumps(at.session_state["order_ledger"]).lower() and "endoscopy" not in json.dumps(at.session_state["events"]).lower(), "nothing claims the order was executed or even written"


def test_t6_a_held_order_whose_release_is_refused_is_still_held_exactly_as_the_resident_left_it(monkeypatch, tmp_path):
    """The guided form used to CONSUME the held order at render time, before the turn that runs it: a refusal then lost the hold. The consumption now happens inside the turn."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    before = _execute(at, page.UNSUPPORTED)
    assert json.loads(before.replace("NaN", "null"))["pending_reasoning"], "the order was held for its reasoning before the refused release"
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert at.session_state["pending_reasoning"], "the hold and its prompt are still there"
    assert any("ORDER HELD" in str(event.get("text")) for event in at.session_state["events"])


def test_t7_a_session_that_has_not_committed_yet_keeps_the_legacy_turn_clean_abort(monkeypatch, tmp_path):
    """FD-STOP-04, unchanged and explicit: before the first commit nothing authoritative was ever shown, so a refusal is PRECOMMIT_ABORT and the legacy turn that ran stands."""
    at = stop._open(monkeypatch, tmp_path, CASES[0])
    page._order(at, page.UNSUPPORTED)
    site = stop._site(at)
    assert site.halted and not site.minutes_committed
    record = stop._record(at)
    assert record["lifecycle"] == se.PRECOMMIT_ABORT and record["continuation_allowed"] is True
    assert page._minute(at) > 0, "the legacy turn ran and stays"
    assert ra.PROVENANCE_ANCHOR_KEY not in at.session_state["state"], "nothing authoritative ever happened, so there is no anchor"
    _no_turn_left_open(at)
    assert not any(str(item.value).startswith("DEVELOPMENT AUTHORITY EXPERIMENT HALTED") for item in at.warning)
    page._order(at, "Reassess in 10 minutes.")                                  # the untouched legacy encounter continues
    assert not at.exception


def test_t7b_a_first_commit_the_store_cannot_make_durable_is_withdrawn_and_the_legacy_encounter_continues(monkeypatch, tmp_path):
    at = stop._open(monkeypatch, tmp_path, CASES[0])
    stop._inject_persistence(monkeypatch)
    page._ask(at, "What brought you in today?")
    site = stop._site(at)
    assert site.halted and not site.minutes_committed, "the commit was withdrawn: nothing is authoritative"
    assert stop._record(at)["lifecycle"] == se.PRECOMMIT_ABORT and stop._record(at)["continuation_allowed"] is True
    assert ra.PROVENANCE_ANCHOR_KEY not in at.session_state["state"] and page._minute(at) > 0
    _no_turn_left_open(at)


def test_t9_a_lineage_the_settlement_reveals_is_refused_before_the_commit_never_after_it(monkeypatch, tmp_path):
    """A committed minute is never rewritten (faculty decision F), so the settled lineage is judged BEFORE the commit: a contradiction is the refusal of the turn, and there is no commit to take back."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    monkeypatch.setattr(ra, "lineage_violations", lambda rows: [{"order_id": "t:0", "class": "fluid", "fate": "EXECUTED", "link": "broken"}])
    before = _execute(at, ORDER)
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert site.halt_reason.startswith(ra.PROVENANCE_CONTRADICTION), site.halt_reason
    assert not [item for item in site.artifact()["minutes"] if item.get("committed") and ra._as_int(item.get("minute")) > last], "judged BEFORE the commit: nothing past the last authoritative minute was ever committed"
    assert stop._record(at)["stop_class"] == se.STOP_UNSUPPORTED_ACTION and stop._record(at)["last_authoritative_minute"] == last


def test_t10_a_zero_minute_turn_whose_settled_class_the_mapping_cannot_represent_is_refused_before_it_is_recorded(monkeypatch, tmp_path):
    """The P3-48 gap, closed for the quiet turn too: an order the engine does not model produces no action, so only the settled ledger names it. It used to be recorded and executed on the real
    encounter before the halt; now the IV line never happened to it."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), _anchor(at)
    quiet_before = len(site.no_advance_turns)
    monkeypatch.setattr(ra, "unsupported_in_settlement", lambda rows: ("an_unmodelled_class",))
    before = _execute(at, "Place an IV line.")
    _refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert site.halt_reason.startswith(ra.PROVENANCE_CONTRADICTION) and len(site.no_advance_turns) == quiet_before, "refused before the zero-minute turn was recorded as a turn of the experiment"
    assert len(at.session_state["order_ledger"]) == len(json.loads(before.replace("NaN", "null"))["order_ledger"]), "the refused IV line added no row to the order ledger"


# -- the static tripwire: no clock-moving route may leave the transaction -----------------------------------------------------------------------------------

def _enclosing_turn_scopes(tree):
    """For every call in app.py: the ``_authority_turn(...)`` context managers it is lexically inside (the names of the routes)."""
    import ast
    found = []

    def visit(node, scopes):
        if isinstance(node, ast.With):
            added = [ast.unparse(item.context_expr) for item in node.items if ast.unparse(item.context_expr).startswith("_authority_turn(")]
            for child in node.body:
                visit(child, scopes + added)
            for item in node.items:
                visit(item.context_expr, scopes)
            return
        if isinstance(node, ast.Call):
            found.append((ast.unparse(node.func), node.lineno, tuple(scopes)))
        for child in ast.iter_child_nodes(node):
            visit(child, scopes)
    visit(tree, [])
    return found


def test_t13_every_route_that_can_move_the_clock_runs_inside_an_authority_turn_and_a_new_one_fails_here():
    import ast
    tree = ast.parse((stop.ROOT / "app.py").read_text(encoding="utf-8"))
    calls = _enclosing_turn_scopes(tree)
    spend = [scopes for name, line, scopes in calls if name == "spend_clinical_time"]
    assert len(spend) == 3 and all(len(scopes) == 1 for scopes in spend), "the question, the topic and the examination each run inside their own authority turn"
    assert sorted(scope for scopes in spend for scope in scopes) == ["_authority_turn('examination')", "_authority_turn('history_question')", "_authority_turn('history_topic')"]
    bodies = [(line, scopes) for name, line, scopes in calls if name == "_process_encounter_submission_turn"]
    assert len(bodies) == 1 and bodies[0][1] == ("_authority_turn('order_turn')",), "the order turn body runs only inside the order authority turn"
    # and the only callers of the two engine entry points are the chokepoints these scopes cover (the guard of P3-253A pins the same set from the other side)
    assert stop._functions_calling(tree, {"advance_clinical_time"}) == {"spend_clinical_time"}
    assert stop._functions_calling(tree, {"execute_bundle"}) == {"_process_encounter_submission_turn"}
    assert stop._functions_calling(tree, {"_authority_turn"}) == {"_clinical_encounter_workspace", "_process_encounter_submission"}
    # the verdict is asked at the two places the authority judges
    checks = sorted(name for name, line, scopes in calls if name == "_authority_turn_check")
    assert len(checks) == 3
    assert stop._functions_calling(tree, {"_authority_turn_check"}) == {"spend_clinical_time", "_process_encounter_submission_turn"}


# -- flags off -----------------------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_t8_with_every_authority_flag_off_there_is_no_turn_no_anchor_and_no_authority_key(monkeypatch, case):
    at = page._open(monkeypatch, case, shadow=True, dry=False, authority=None)
    for step in (lambda: page._ask(at, "What brought you in today?"), lambda: page._order(at, "Place an IV line."), lambda: page._order(at, ORDER), lambda: page._examine(at)):
        step()
        _no_turn_left_open(at)
        assert ra.PROVENANCE_ANCHOR_KEY not in at.session_state["state"]
    assert not at.session_state.get(ra.SITE_KEY) and not at.session_state.get(se.SESSION_KEY)
    assert not any(str(item.value).startswith("DEVELOPMENT AUTHORITY") for item in at.warning)


# -- P3-274: lost state, every combination, fail closed ------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def failed(tmp_path_factory):
    """ONE encounter that was authoritative and whose next turn was refused: its fields are copied into each reopened page, nothing here mutates it."""
    directory = tmp_path_factory.mktemp("turn-recovery")
    mp = pytest.MonkeyPatch()
    try:
        at = stop._open(mp, directory, CASES[0])
        site = stop._first_commit(at)
        page._order(at, ORDER)
        last = max(site.minutes_committed)
        page._order(at, page.UNSUPPORTED)
        assert site.halted and site.halt_reason.startswith(ra.UNSUPPORTED_AUTHORITY_ACTION) and page._minute(at) == last
        mp.undo()
        yield {"at": at, "site": site, "last": last, "dir": directory}
    finally:
        mp.undo()


def _reopen(monkeypatch, old, *, flags_on, store_dir=None, drop=(), advance=0, strip_anchor=False):
    """A saved encounter reopened in a new page session: ONLY the saved fields come back (never the site, never the artifact object), after the named losses."""
    page._clean(monkeypatch, "gi_bleed_57m", shadow=flags_on, dry=False, authority=(str(store_dir) if flags_on else None))
    from streamlit.testing.v1 import AppTest
    new = AppTest.from_file(page.APP, default_timeout=600)
    new.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    new.session_state["_shared_access_granted"] = True
    for key in SESSION_FIELDS:
        if key in old.session_state and key not in drop:
            new.session_state[key] = deepcopy(old.session_state[key])
    state = new.session_state["state"]
    if strip_anchor:
        state.pop(ra.PROVENANCE_ANCHOR_KEY, None)
    if advance:
        state["sim_time"] = int(state["sim_time"]) + advance                      # the legacy engine ran on past the last authoritative minute
    new.run()
    assert not new.exception, [str(item.value)[:300] for item in new.exception]
    return new


def _stopped_and_blocked(new, monkeypatch, *, class_in=None):
    decision = se.continuation_guard(new.session_state, new.session_state["state"], environ={})
    assert decision["allowed"] is False and decision["lifecycle"] == se.INVALID_FOR_CONTINUATION and decision["legacy_fallback_allowed"] is False, decision
    if class_in:
        assert decision["stop_class"] in class_in, decision["stop_class"]
    controls = stop._controls(new)
    assert not (controls["ask_box"] or controls["order_box"] or controls["examine"] or controls["ecg"] or controls["send"] or controls["ask_button"] or controls["complete_enabled"]), controls
    spy = stop.EngineSpy(monkeypatch)
    before = _encounter(new)
    for attempt in (lambda: page._ask(new, "Where does it hurt?"), lambda: page._order(new, "Reassess in 10 minutes."), lambda: page._examine(new)):
        with pytest.raises(StopIteration):
            attempt()
    new.run()
    assert spy.calls == [] and _encounter(new) == before, "a stopped encounter never reaches the engine and never moves"


@pytest.mark.parametrize("flags_on", (True, False), ids=("flags_on", "flags_off"))
@pytest.mark.parametrize("record_kept", (True, False), ids=("record_kept", "record_lost"))
@pytest.mark.parametrize("advance", (0, 25), ids=("clock_as_left", "legacy_ran_on"))
def test_r1_every_combination_of_a_lost_record_a_lost_site_and_a_legacy_clock_that_ran_on_is_a_stop(failed, monkeypatch, tmp_path, flags_on, record_kept, advance):
    """The site is ALWAYS lost on a reopen. The record may be lost too, the flags may be off, and the legacy engine may have run on past the last authoritative minute: the provenance anchor
    carried by the encounter itself is what still says authority occurred."""
    new = _reopen(monkeypatch, failed["at"], flags_on=flags_on, store_dir=tmp_path / "empty-store", drop=() if record_kept else (se.SESSION_KEY,), advance=advance)
    assert _anchor(new)["last_authority_minute"] == failed["last"], "the anchor survived the reopen"
    _stopped_and_blocked(new, monkeypatch, class_in=(se.STOP_UNSUPPORTED_ACTION, se.STOP_PROVENANCE, se.STOP_RESUMED))


@pytest.mark.parametrize("artifact", ("present", "missing", "corrupt"))
def test_r2_an_encounter_that_lost_its_record_and_its_site_is_stopped_whatever_the_artifact_says(failed, monkeypatch, tmp_path, artifact):
    """Flags on, the record gone and the site gone, with the stored artifact present, missing or corrupt: the anchor alone decides, and a corrupt or absent artifact can only make it stricter."""
    store_dir = tmp_path / "store"
    source = failed["dir"] / "store"
    if artifact != "missing" and source.exists():
        import shutil
        shutil.copytree(source, store_dir)
        if artifact == "corrupt":
            for path in store_dir.rglob("*.json"):
                path.write_text("{ this is not json", encoding="utf-8")
    new = _reopen(monkeypatch, failed["at"], flags_on=True, store_dir=store_dir, drop=(se.SESSION_KEY,), advance=10)
    _stopped_and_blocked(new, monkeypatch, class_in=(se.STOP_UNSUPPORTED_ACTION, se.STOP_PROVENANCE, se.STOP_RESUMED))


def test_r3_an_encounter_that_was_authoritative_and_simply_lost_its_site_and_record_is_stopped_even_with_no_failure(monkeypatch, tmp_path):
    """No failure at all: an ACTIVE encounter reopened with the flags OFF, no record and no site. Before this cycle the legacy engine continued it."""
    at, site = _two_commits(monkeypatch, tmp_path, CASES[0])
    assert stop._record(at)["lifecycle"] == se.ACTIVE_AUTHORITY
    for flags_on in (False, True):
        new = _reopen(monkeypatch, at, flags_on=flags_on, store_dir=tmp_path / "other-store", drop=(se.SESSION_KEY,), advance=15)
        record = _stopped_and_blocked(new, monkeypatch, class_in=(se.STOP_PROVENANCE, se.STOP_RESUMED)) or new.session_state[se.SESSION_KEY]
    assert ra.PROVENANCE_LOST in new.session_state[se.SESSION_KEY]["halt_reason"] or ra.RESUMED_WITHOUT_SITE in new.session_state[se.SESSION_KEY]["halt_reason"]


class Saved:
    """The saved fields of an encounter, copied: all that ``_reopen`` reads of the page it comes from (an ``AppTest`` itself cannot be copied)."""

    def __init__(self, at):
        self.session_state = {key: deepcopy(at.session_state[key]) for key in SESSION_FIELDS if key in at.session_state}


def test_r4_a_corrupted_anchor_and_a_corrupted_record_are_each_a_stop(failed, monkeypatch, tmp_path):
    tampered = Saved(failed["at"])
    state = tampered.session_state["state"]
    state[ra.PROVENANCE_ANCHOR_KEY] = dict(state[ra.PROVENANCE_ANCHOR_KEY], commits=99)          # a half-edit: the digest no longer recomputes
    new = _reopen(monkeypatch, tampered, flags_on=False, drop=(se.SESSION_KEY,))
    _stopped_and_blocked(new, monkeypatch, class_in=(se.STOP_PROVENANCE,))
    bad_record = Saved(failed["at"])
    bad_record.session_state[se.SESSION_KEY] = dict(bad_record.session_state[se.SESSION_KEY], last_authoritative_minute=1)
    new = _reopen(monkeypatch, bad_record, flags_on=False)
    _stopped_and_blocked(new, monkeypatch, class_in=(se.STOP_STALE_OR_CONFLICTING, se.STOP_PROVENANCE))


def test_r5_a_record_and_an_anchor_that_disagree_are_a_stop_not_a_choice_of_the_milder(failed, monkeypatch):
    other = Saved(failed["at"])
    state = other.session_state["state"]
    anchor = {key: value for key, value in state[ra.PROVENANCE_ANCHOR_KEY].items() if key != "anchor_digest"}
    anchor["encounter_id"] = "another-encounter"
    state[ra.PROVENANCE_ANCHOR_KEY] = {**anchor, "anchor_digest": ra.digest_of(anchor)}          # a well-formed anchor of ANOTHER encounter
    new = _reopen(monkeypatch, other, flags_on=False)
    _stopped_and_blocked(new, monkeypatch, class_in=(se.STOP_STALE_OR_CONFLICTING, se.STOP_PROVENANCE, se.STOP_UNSUPPORTED_ACTION))


# -- the declared limits of the anchor (never silently better than they are) ----------------------------------------------------------------------------

def test_r6_declared_limit_an_encounter_that_lost_everything_including_its_anchor_is_not_recognisable(failed, monkeypatch, tmp_path):
    """The one combination no evidence remains for: no anchor, no record, no site, no artifact reachable (flags off). The encounter itself says nothing. This is a DECLARED limit, pinned so that
    nobody mistakes the anchor for proof against an encounter that was rebuilt from nothing; the durable-store backstop (flags on) is tested below."""
    new = _reopen(monkeypatch, failed["at"], flags_on=False, drop=(se.SESSION_KEY,), advance=12, strip_anchor=True)
    assert (new.session_state.get(se.SESSION_KEY) or {}).get("lifecycle") != se.INVALID_FOR_CONTINUATION
    assert se.continuation_guard(new.session_state, new.session_state["state"], environ={})["allowed"] is True


def test_r6b_the_durable_store_still_recognises_an_anchorless_encounter_whose_clock_is_where_authority_left_it(failed, monkeypatch, tmp_path):
    """The backstop that existed before the anchor: case, minute and committed pressures. It does not survive a legacy engine that ran on (the declared limit above), and it needs the flags on."""
    source = failed["dir"] / "store"
    if not source.exists():
        pytest.skip("the failed encounter's store is not on disk in this environment")
    import shutil
    store_dir = tmp_path / "store"
    shutil.copytree(source, store_dir)
    new = _reopen(monkeypatch, failed["at"], flags_on=True, store_dir=store_dir, drop=(se.SESSION_KEY,), strip_anchor=True, advance=0)
    _stopped_and_blocked(new, monkeypatch)
