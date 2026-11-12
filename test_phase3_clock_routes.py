"""P3-215 and P3-216: every route by which the engine's clock moves reaches the Phase-3 layer through ONE hook, and a turn of several simulated minutes is
validated at EVERY minute of it.

TEST-SIDE. Nothing here enables an authority: every commit below is made on a copy, through the test-only approval pattern of the P3-28 certification, and the
page's real behavior with every flag off is proved in ``test_phase3_pair_page.py``.

* P3-215 inventory: the writers of ``sim_time`` are enumerated from the source, the page's callers of the two family-engine entry points are enumerated from
  ``app.py``, and a new writer or a new caller fails a test instead of passing unseen.
* P3-215A: the one hook (``runtime_authority_pair.after_clock_moved``) is dormant by default, opens one dry evaluator per encounter and per case, never raises
  into the turn and never writes the state.
* P3-215 at the authority site: the clinical-time route, the unknown route, the turn that does not advance the clock.
* P3-216: the granularity. ``VALIDATED_ATOMIC_INTERVAL``: every minute of a turn is validated with the same checks, one commit of the engine's end state, a failure at
  minute k commits nothing and no later minute becomes authoritative.
"""
import ast
import dataclasses
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import observable_view as view
import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_shadow as rs
import runtime_shadow_evidence as ev
from family_engine import advance_clinical_time

ROOT = Path(__file__).resolve().parent
CASE, OTHER_GI, NOT_GI = "gi_bleed_57m", "gi_bleed_72f", "opioid_35m"
TEST_ONLY_SNAPSHOT = {"id": "test_only_clock_route_point", "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID, "parameters": {"test_only_placeholder": 1.0}}
STORE_DIR = tempfile.mkdtemp(prefix="phase3-clock-routes-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"], ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE, store.STORE_FLAG: STORE_DIR}
DRY = {rs.FLAG: rs.MODE_SHADOW_COMPARE, pair.DRY_FLAG: pair.DRY_ON}


@pytest.fixture
def approved(monkeypatch, tmp_path):
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    directory = tmp_path / "phase3_authority"
    monkeypatch.setenv(store.STORE_FLAG, str(directory))
    return {**BEST, store.STORE_FLAG: str(directory)}


@pytest.fixture(scope="module")
def bound():
    return pair.bind(str(ROOT))


def _spend(encounter, minutes, label="history question"):
    """What the page's ``spend_clinical_time`` does to the engine and the shadow, without the page: capture, let the time pass, observe it."""
    before = encounter.shadow.capture(encounter.state)
    result = advance_clinical_time(encounter.state, minutes, label=label)
    encounter.shadow.observe_time(before, encounter.state, result)
    return before


def _turn(encounter, text):
    """One order turn as the headless harness plays it: the state before, the entry, and the actions the engine received."""
    before = encounter.shadow.capture(encounter.state)
    entry = encounter.order(text)
    return before, entry, [dict(item) for item in entry["orders"]]


@pytest.fixture(scope="module")
def activity():
    """A real GI encounter: five minutes of history-taking from the arrival."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before = _spend(encounter, 5)
    return {"arrival": arrival, "before": before, "after": deepcopy(encounter.state), "session": encounter.shadow, "encounter": encounter}


@pytest.fixture(scope="module")
def iv_first():
    """The commonest first order: an IV line, as the very first turn. The engine executes it and the clock does not move."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before, entry, ran = _turn(encounter, "Place an IV line.")
    return {"arrival": arrival, "before": before, "after": deepcopy(encounter.state), "session": encounter.shadow, "ran": ran, "entry": entry}


# -- P3-215: the inventory, reproduced from the source -----------------------------------------------------------------------------------------------

def _writers_of_the_clock():
    """Every (file, function) that assigns ``<x>["sim_time"]`` in the repository's own source (tests, the validation corpus and the docs excluded)."""
    found = set()
    skip = ("validation", "docs", "scripts", ".git", "clinical_physiology")
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT).parts
        if relative[0] in skip or path.name.startswith(("test_", "regression_")) or relative[0] == "clinical_core":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))

        def walk(node, function):
            for child in ast.iter_child_nodes(node):
                name = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else function
                walk(child, name)
                if isinstance(child, (ast.Assign, ast.AugAssign)):
                    for target in (child.targets if isinstance(child, ast.Assign) else [child.target]):
                        if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) and target.slice.value == "sim_time":
                            found.add((path.name, function))
        walk(tree, None)
    return found


def test_t1_the_writers_of_the_clock_are_exactly_the_known_ones_and_only_two_can_reach_a_gi_encounter():
    """A new writer of ``sim_time`` is a new route the dry evaluation does not see: it fails here instead of passing unseen.

    The two family-engine writers are the only ones a GI encounter reaches. The legacy engine's page function, the coupled and the generated engine run
    for cases whose ``engine_family`` is not ``gi_bleed``, for which the authority site and the dry evaluation refuse the case (``case_eligible``)."""
    assert _writers_of_the_clock() == {("family_engine.py", "advance_clinical_time"), ("family_engine.py", "execute_family_bundle"),
                                       ("app.py", "_advance_with_timed_fluids"), ("coupled_encounter.py", "tick"), ("generated_engine.py", "_minute")}
    assert ra.AUTHORITY_FAMILY == "gi_bleed" and set(ra.AUTHORITY_CASES) == {CASE, OTHER_GI}


def _functions_calling(tree, name):
    out = set()
    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] == name:
                out.add(function.name)
    return out


def test_t2_every_page_route_that_moves_the_family_clock_calls_the_one_hook():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    # the two family-engine entry points that move the clock are reached from ONE page function each (plus the page's own legacy branch of execute_bundle)
    assert _functions_calling(tree, "advance_clinical_time") == {"spend_clinical_time"}
    assert _functions_calling(tree, "execute_family_bundle") == {"execute_bundle"}
    assert len([n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "execute_bundle"]) == 1
    callers = _functions_calling(tree, "execute_bundle")
    assert len(callers) == 1
    # the three places an information activity spends time all go through the one function
    assert len([n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "spend_clinical_time"]) == 3
    routes, hooked = set(), set()
    for function in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)):
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "_after_the_clock_moved":
                hooked.add(function.name)
                route = next(keyword.value for keyword in node.keywords if keyword.arg == "route")
                assert isinstance(route, ast.Constant), "a route is a literal the audit can read"
                routes.add(route.value)
    assert routes == set(ra.KNOWN_ROUTES) == {ra.ORDER_TURN, ra.CLINICAL_TIME}
    assert hooked == {"spend_clinical_time"} | callers, hooked


def test_t3_the_page_hook_orchestrates_and_decides_nothing():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    hook = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_after_the_clock_moved")
    source = ast.unparse(hook)
    assert source.count("runtime_authority.after_clock_moved(") == 1 and "runtime_authority_pair" not in source
    # the only condition is "no shadow session, nothing to do"; the flags, the case and the authority are the layer's decisions
    conditions = [ast.unparse(node.test) for node in ast.walk(hook) if isinstance(node, ast.If)]
    assert conditions == ["shadow is None"], conditions
    # app.py never reads a dry artifact, a verdict or a record back
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    for forbidden in ("DRY_ARTIFACT_KEY", "phase3_pair_dry_artifact", ".would_commit", "WOULD_COMMIT", "WOULD_ABORT", "dry_evaluator_for"):
        assert forbidden not in text, forbidden


# -- P3-215A: the hook ------------------------------------------------------------------------------------------------------------------------------

def test_t4_dormant_by_default_every_flag_combination_but_one_does_nothing(activity):
    session = activity["session"]
    for environ in ({}, {rs.FLAG: rs.MODE_SHADOW_COMPARE}, {pair.DRY_FLAG: pair.DRY_ON}, {rs.FLAG: rs.MODE_SHADOW_COMPARE, pair.DRY_FLAG: "yes"},
                    {rs.FLAG: rs.MODE_OFF, pair.DRY_FLAG: pair.DRY_ON}):
        held = {}
        assert pair.after_clock_moved(held, session, activity["before"], deepcopy(activity["after"]), None, None, ra.CLINICAL_TIME, environ=environ) is None
        assert held == {}, environ                                            # not even a refusal is written: with the flag off nothing exists
        assert pair.dry_evaluator_for(held, session, environ=environ) is None and held == {}
    assert pair.dry_run_enabled(DRY) and not pair.dry_run_enabled({})


def test_t5_the_dry_flag_opens_one_evaluator_per_encounter_and_a_new_encounter_gets_its_own(activity):
    held = {}
    state = deepcopy(activity["after"])
    assert pair.after_clock_moved(held, activity["session"], activity["before"], state, None, None, ra.CLINICAL_TIME, environ=DRY) is None
    evaluator = held[pair.DRY_KEY][1]
    assert isinstance(evaluator, pair.PairDryEvaluator) and held[pair.DRY_REFUSAL_KEY] is None
    assert pair.dry_evaluator_for(held, activity["session"], environ=DRY) is evaluator          # the same encounter keeps its evaluator
    assert held[pair.DRY_ARTIFACT_KEY]["routes"] == [ra.CLINICAL_TIME] and held[pair.DRY_ARTIFACT_KEY]["minutes_evaluated"] == 1
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        another = acceptance.Encounter(CASE)
    second = pair.dry_evaluator_for(held, another.shadow, environ=DRY)
    assert second is not None and second is not evaluator and held[pair.DRY_KEY][0] is another.shadow    # two patients are never mixed in one evaluator
    pair.forget(held)
    assert held == {}


def test_t6_a_case_that_is_not_one_of_the_two_gi_cases_gets_no_evaluator_and_the_reason_is_remembered_once():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(NOT_GI)
    held = {}
    assert pair.dry_evaluator_for(held, encounter.shadow, environ=DRY) is None
    assert held[pair.DRY_REFUSAL_KEY] == pair.CASE_NOT_ELIGIBLE and held[pair.DRY_KEY] == (encounter.shadow, None)
    assert pair.after_clock_moved(held, encounter.shadow, None, deepcopy(encounter.state), None, None, ra.CLINICAL_TIME, environ=DRY) is None
    assert pair.DRY_ARTIFACT_KEY not in held


def test_t7_a_treated_arrival_is_not_an_eligible_arrival_and_opens_nothing():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        encounter.order("Give 500 mL normal saline over 5 minutes.")
        resumed = rs.ShadowSession.start(encounter.state, environ=DRY)           # the page resumed a case that was already treated
    held = {}
    assert resumed is not None and pair.dry_evaluator_for(held, resumed, environ=DRY) is None
    assert held[pair.DRY_REFUSAL_KEY] == pair.ARRIVAL_NOT_ELIGIBLE


def test_t8_the_clinical_time_route_is_evaluated_like_an_order_turn_and_the_state_is_never_touched(activity):
    held, state = {}, deepcopy(activity["after"])
    digest = ra.digest_of(state)
    pair.after_clock_moved(held, activity["session"], activity["before"], state, None, None, ra.CLINICAL_TIME, environ=DRY)
    record = held[pair.DRY_KEY][1].records[-1]
    assert record["route"] == ra.CLINICAL_TIME and record["minute"] == 5 and record["verdict"] == pair.WOULD_COMMIT, record["failed_checks"]
    assert record["action_kinds"] == [] and [row["minute"] for row in record["interval"]] == [1, 2, 3, 4, 5]
    assert ra.digest_of(state) == digest and not held[pair.DRY_KEY][1].violations
    # the page's pair of names is the layer's pair of names
    assert record["route"] in ra.KNOWN_ROUTES


def test_t9_a_hook_failure_is_recorded_and_never_raised_into_the_turn(activity, monkeypatch):
    held, state = {}, deepcopy(activity["after"])

    def boom(*args, **kwargs):
        raise RuntimeError("the evaluator broke")
    monkeypatch.setattr(pair.PairDryEvaluator, "minute", boom)
    assert pair.after_clock_moved(held, activity["session"], activity["before"], state, None, None, ra.CLINICAL_TIME, environ=DRY) is None
    assert held[pair.DRY_REFUSAL_KEY] == "HOOK_FAILED: RuntimeError" and state == activity["after"]
    pair.after_orders_settled({}, activity["session"], [], environ=DRY)             # settling with nothing open is a no-op, not an error


def test_t10_an_open_real_site_suppresses_the_dry_evaluation_so_a_minute_is_never_evaluated_after_it_was_written(activity):
    held = {ra.SITE_KEY: object()}
    pair.after_clock_moved(held, activity["session"], activity["before"], deepcopy(activity["after"]), None, None, ra.ORDER_TURN, environ=DRY)
    assert pair.DRY_KEY not in held and pair.DRY_ARTIFACT_KEY not in held


# -- P3-215 at the authority site ------------------------------------------------------------------------------------------------------------------

def _site(arrival, approved):
    site = ra.open_site(arrival, environ=approved)
    assert site is not None
    return site


def test_s1_the_clinical_time_route_commits_the_pressure_domain_only_and_is_settled_by_construction(activity, approved):
    site = _site(activity["arrival"], approved)
    after = deepcopy(activity["after"])
    prepared = site.minute(activity["before"], after, activity["session"], None, "act-1", ra.CLINICAL_TIME)
    assert prepared is not None and site.minutes_committed == (5,) and not site.halted
    moved = ra.AuthoritySite._moved(after, prepared)
    assert moved <= {"sbp", "dbp", "map"}, moved
    row = site.artifact()["minutes"][-1] if "minutes" in site.artifact() else None
    assert row is not None and row["route"] == ra.CLINICAL_TIME and row["provenance_settled"] is True and row["action_lineage"] == []
    # the legacy turn's own state is the same object it was handed: the site returns a NEW mapping
    assert after == activity["after"]


def test_s2_an_action_on_the_clinical_time_route_is_a_contradiction_and_halts_visibly(activity, approved):
    site = _site(activity["arrival"], approved)
    assert site.minute(activity["before"], deepcopy(activity["after"]), activity["session"], [{"type": "fluid", "volume_ml": 250}], "act-1", ra.CLINICAL_TIME) is None
    assert site.halted and ra.UNSUPPORTED_AUTHORITY_ACTION in site.halt_reason and not site.minutes_committed


def test_s3_an_unknown_route_is_refused_and_halts(activity, approved):
    for route in ("telepathy", "", None, "ORDER_TURN"):
        site = _site(activity["arrival"], approved)
        assert site.minute(activity["before"], deepcopy(activity["after"]), activity["session"], None, "x", route) is None
        assert site.halted and ra.UNKNOWN_ROUTE in site.halt_reason and not site.minutes_committed, route
    assert ra.KNOWN_ROUTES == (ra.ORDER_TURN, ra.CLINICAL_TIME)


def test_s4_an_iv_line_turn_that_does_not_move_the_clock_is_recorded_and_the_experiment_goes_on(iv_first, approved):
    site = _site(iv_first["arrival"], approved)
    assert iv_first["after"]["sim_time"] == iv_first["before"]["sim_time"] == 0
    out = site.minute(iv_first["before"], deepcopy(iv_first["after"]), iv_first["session"], iv_first["ran"], "iv-1", ra.ORDER_TURN)
    assert out is None and not site.halted and site.minutes_committed == ()
    turn = site.no_advance_turns[-1]
    assert turn["action_kinds"] == ["vascular_access"] and turn["no_common_physiology"][0]["disposition"] == ra.EXECUTED_NO_COMMON_PHYSIOLOGY
    assert turn["no_common_physiology"][0]["contributor"] is None and turn["no_common_physiology"][0]["physiological_mutation"] is False
    assert site.artifact()["no_advance_turns"][-1]["outcome"] == ra.NO_ADVANCE_TURN


def test_s5_a_zero_advance_turn_with_an_unsupported_class_still_halts(iv_first, approved):
    site = _site(iv_first["arrival"], approved)
    ran = [{"order_id": "t0:0", "type": "intubation", "fate": "EXECUTED"}]
    assert site.minute(iv_first["before"], deepcopy(iv_first["after"]), iv_first["session"], ran, "bad", ra.ORDER_TURN) is None
    assert site.halted and ra.UNSUPPORTED_AUTHORITY_ACTION in site.halt_reason and site.no_advance_turns == []
    # mixed: an IV line AND an unsupported class is unsupported, the acknowledgement does not cover its neighbor
    site = _site(iv_first["arrival"], approved)
    ran = [{"order_id": "t0:0", "type": "vascular_access", "fate": "EXECUTED"}, {"order_id": "t0:1", "type": "intubation", "fate": "EXECUTED"}]
    assert site.minute(iv_first["before"], deepcopy(iv_first["after"]), iv_first["session"], ran, "bad", ra.ORDER_TURN) is None and site.halted


def test_s6_a_turn_whose_pressure_moved_is_not_a_no_advance_turn(iv_first, approved):
    site = _site(iv_first["arrival"], approved)
    moved = deepcopy(iv_first["after"])
    moved["observable"] = {**moved["observable"], "sbp": int(moved["observable"]["sbp"]) + 9}
    out = site.minute(iv_first["before"], moved, iv_first["session"], iv_first["ran"], "iv-1", ra.ORDER_TURN)
    assert site.no_advance_turns == [], "a pressure that moved is never filed as 'nothing happened'"
    assert out is not None or site.halted


def test_s7_a_duplicate_minute_with_no_before_state_is_still_refused_as_the_certified_g7_says(activity, approved):
    site = _site(activity["arrival"], approved)
    assert site.minute(activity["before"], deepcopy(activity["after"]), activity["session"], None, "a", ra.CLINICAL_TIME) is not None
    assert site.minute(None, deepcopy(activity["after"]), activity["session"], [], "b", ra.ORDER_TURN) is None
    assert site.halted and ra.MINUTE_ALREADY_COMMITTED in site.halt_reason and site.no_advance_turns == []


@pytest.fixture
def site_infusion():
    """A fresh 30-minute infusion turn per test: a test that injects a failure into the shadow's record must not contaminate another."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before, entry, ran = _turn(encounter, "Give 500 mL normal saline over 30 minutes.")
    return {"arrival": arrival, "before": before, "after": deepcopy(encounter.state), "session": encounter.shadow, "ran": ran}


@pytest.mark.parametrize("k", (1, 12, 29, 30))
def test_s8_a_failure_at_any_minute_of_a_multi_minute_turn_refuses_the_pressure_commit(site_infusion, approved, k):
    """Found by the probe of this cycle: the certified site filtered the shadow's failures on ``minute == end``, so a failure at minute 12 of a 30-minute turn
    committed minute 30. The whole turn's interval is now the window (NEW-06). Mutant: restoring the old filter makes k = 1, 12 and 29 commit."""
    site = _site(site_infusion["arrival"], approved)
    site_infusion["session"].failures.append(rs.ShadowFailure(k, "mid_interval", "InjectedFailure", "a failure inside the turn's interval", rs.MAPPING_GAP))
    out = site.minute(site_infusion["before"], deepcopy(site_infusion["after"]), site_infusion["session"], site_infusion["ran"], "inf-1", ra.ORDER_TURN)
    assert out is None and site.halted and site.minutes_committed == (), k


def test_s9_a_failure_the_shadow_recorded_before_the_turn_is_judged_by_that_turn_and_a_clean_turn_commits(site_infusion, approved):
    """Superseded reading (the independent review, F3): the window is no longer the turn's minutes, it is EVERY failure not yet judged. A failure stamped at the
    arrival (minute 0) therefore refuses the first turn -- the turn that has not judged it -- instead of escaping a window that started at minute 1. Negative control:
    the same turn with nothing recorded commits."""
    site = _site(site_infusion["arrival"], approved)
    site_infusion["session"].failures.append(rs.ShadowFailure(0, "start", "InjectedFailure", "recorded at the arrival", rs.MAPPING_GAP))
    out = site.minute(site_infusion["before"], deepcopy(site_infusion["after"]), site_infusion["session"], site_infusion["ran"], "inf-1", ra.ORDER_TURN)
    assert out is None and site.halted and site.minutes_committed == ()
    clean = _site(site_infusion["arrival"], approved)
    site_infusion["session"].failures.clear()
    assert clean.minute(site_infusion["before"], deepcopy(site_infusion["after"]), site_infusion["session"], site_infusion["ran"], "inf-1", ra.ORDER_TURN) is not None
    assert clean.minutes_committed == (30,) and clean.failures_judged == 0


# -- P3-216: the granularity -------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def infusion(bound):
    """A real 30-minute infusion: ONE turn, the clock jumps 30 minutes, the legacy engine exposes only the END state. The dry evaluator is fed the way the page's
    hook feeds it, and the shadow is left un-tampered; a test that attacks it does so after."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before, entry, ran = _turn(encounter, "Give 500 mL normal saline over 30 minutes.")
        after = deepcopy(encounter.state)
    dry = pair.PairDryEvaluator(bound, CASE, arrival)
    return {"dry": dry, "before": before, "after": after, "ran": ran, "session": encounter.shadow, "arrival": arrival, "encounter": encounter}


def test_i1_a_multi_minute_infusion_is_validated_at_every_minute_and_committed_once_at_the_end(infusion):
    assert infusion["after"]["sim_time"] == 30 and infusion["before"]["sim_time"] == 0
    record = infusion["dry"].minute(infusion["before"], infusion["after"], infusion["session"], infusion["ran"], "inf-1", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_COMMIT, record["failed_checks"]
    assert [row["minute"] for row in record["interval"]] == list(range(1, 31)) and all(row["ok"] for row in record["interval"])
    assert record["would_write"]["minute"] == 30 and infusion["dry"].would_commit == [30]      # ONE commit, of the end state
    assert pair.GRANULARITY == pair.VALIDATED_ATOMIC_INTERVAL != pair.PER_MINUTE_TRANSACTION
    # the legacy engine showed ONE state for the turn: there is no intermediate legacy minute to commit, which is why a per-minute transaction is not offered
    assert record["legacy"]["sbp"] == infusion["after"]["observable"]["sbp"]


def _break_minute(infusion, k, how):
    """Break exactly minute ``k`` of the shadow's own record of this turn, the way a failure inside the interval would."""
    session = infusion["session"]
    if how == "failure_at_minute":
        session.failures.append(rs.ShadowFailure(k, "mid_interval", "InjectedFailure", "a failure at one minute of the interval", rs.MAPPING_GAP))
        return
    results = session.runner.results
    index = next(position for position, item in enumerate(results) if int(item.minute) == k)
    derived = dict(results[index].derived)
    if how == "no_candidate":
        derived["sbp"] = None
    elif how == "not_one_course":
        name = next(reading for reading in pair.SHARED_READINGS if isinstance(derived.get(reading), (int, float)) and not isinstance(derived.get(reading), bool))
        derived[name] = float(derived[name]) + 7.0
    else:
        raise AssertionError(how)
    results[index] = dataclasses.replace(results[index], derived=derived)


@pytest.mark.parametrize("how", ("no_candidate", "failure_at_minute", "not_one_course"))
@pytest.mark.parametrize("k", (1, 15, 29))
def test_i2_a_failure_at_an_intermediate_minute_commits_nothing_and_no_later_minute_becomes_authoritative(bound, k, how):
    """Hidden-intermediate-minute attack: the END minute (30) is intact, so a check on the end state alone would pass. The interval check must not."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before, entry, ran = _turn(encounter, "Give 500 mL normal saline over 30 minutes.")
    dry = pair.PairDryEvaluator(bound, CASE, arrival)
    _break_minute({"session": encounter.shadow}, k, how)
    record = dry.minute(before, deepcopy(encounter.state), encounter.shadow, ran, "inf-1", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_ABORT and "interval_minutes_validated" in record["failed_checks"], record["failed_checks"]
    detail = record["detail"]["interval_minutes_validated"]
    assert detail["first_failed_minute"] == k and k < 30, detail
    assert record["would_write"] is None and dry.would_commit == [] and dry.halt["authority_had_begun"] is False
    # no silent continuation: the next turn (a clinical-time minute) is HALTED, never a WOULD_COMMIT
    follow = dry.minute(deepcopy(encounter.state), deepcopy(encounter.state), encounter.shadow, None, "next", ra.CLINICAL_TIME)
    assert follow["verdict"] == pair.HALTED and dry.would_commit == []


def test_i3_failure_after_authority_had_begun_hard_stops_and_the_earlier_commit_is_not_rewritten(bound):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before, entry, ran = _turn(encounter, "Give 250 mL normal saline over 5 minutes.")
    dry = pair.PairDryEvaluator(bound, CASE, arrival)
    first = dry.minute(before, deepcopy(encounter.state), encounter.shadow, ran, "t1", ra.ORDER_TURN)
    assert first["verdict"] == pair.WOULD_COMMIT and dry.would_commit == [5]
    before2 = encounter.shadow.capture(encounter.state)
    result = advance_clinical_time(encounter.state, 10, label="examination")
    encounter.shadow.observe_time(before2, encounter.state, result)
    _break_minute({"session": encounter.shadow}, 9, "no_candidate")
    second = dry.minute(before2, deepcopy(encounter.state), encounter.shadow, None, "t2", ra.CLINICAL_TIME)
    assert second["verdict"] == pair.WOULD_ABORT and second["detail"]["interval_minutes_validated"]["first_failed_minute"] == 9
    assert dry.would_commit == [5] and dry.halt["authority_had_begun"] is True and "INVALID_FOR_CONTINUATION" in dry.halt["consequence"]
    assert dry.summary()["first_would_commit"] == dry.summary()["last_would_commit"] == 5


def test_i4_a_collapse_boundary_crossed_in_the_middle_of_a_turn_is_not_hidden_by_a_clear_end_state(infusion):
    """The boundary guard reads EVERY minute since the last cleared one, not only the minute that would be committed."""
    dry = infusion["dry"]
    dry.runner.mirror(infusion["session"].mirrored)
    dry.runner.advance(30, state=infusion["session"]._mapping_state())
    dry._channels = {}
    for row in pair.fam.run_channels(dry.runner):
        dry._channels[row["minute"]] = row
    middle = dry._channels[12]
    middle["channels"] = {**middle["channels"], "collapse_state_index": pair.ESTABLISHED}
    boundary = dry._boundary(30)
    assert boundary["clear"] is False and boundary["first_established_minute"] == 12
    # a minute the run cannot show is not a cleared minute either: the guard fails closed
    del dry._channels[20]
    assert dry._boundary(30)["minutes_not_shown"] == [20]


def test_i5_the_experimental_window_ends_at_the_predefined_limit_and_a_caller_cannot_lengthen_it(bound, infusion):
    shorter = pair.PairDryEvaluator(bound, CASE, infusion["arrival"], time_limit=10)
    assert shorter.time_limit == 10
    record = shorter.minute(infusion["before"], infusion["after"], infusion["session"], infusion["ran"], "inf", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_ABORT and "window_open" in record["failed_checks"]
    assert pair.PairDryEvaluator(bound, CASE, infusion["arrival"], time_limit=10 ** 6).time_limit == pair.TIME_LIMIT_MIN == 240


def test_i6_an_iv_line_turn_in_the_evaluator_is_a_no_advance_turn_not_an_abort_and_an_unsupported_one_is(bound, iv_first):
    dry = pair.PairDryEvaluator(bound, CASE, iv_first["arrival"])
    record = dry.minute(iv_first["before"], deepcopy(iv_first["after"]), iv_first["session"], iv_first["ran"], "iv", ra.ORDER_TURN)
    assert record["verdict"] == pair.NO_ADVANCE and dry.halt is None and dry.would_commit == []
    assert record["no_common_physiology"][0]["disposition"] == ra.EXECUTED_NO_COMMON_PHYSIOLOGY and dry.summary()["no_advance_turns"] == 1
    bad = pair.PairDryEvaluator(bound, CASE, iv_first["arrival"])
    record = bad.minute(iv_first["before"], deepcopy(iv_first["after"]), iv_first["session"], [{"order_id": "t0:0", "type": "intubation", "fate": "EXECUTED"}], "x", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_ABORT and "supported_management" in record["failed_checks"]


def test_i7_an_unknown_route_is_an_abort_in_the_evaluator_too(bound, activity):
    dry = pair.PairDryEvaluator(bound, CASE, activity["arrival"])
    record = dry.minute(activity["before"], deepcopy(activity["after"]), activity["session"], None, "x", "a_route_nobody_declared")
    assert record["verdict"] == pair.WOULD_ABORT and "turn_has_a_transaction_site" in record["failed_checks"]


def test_i8_the_overlay_view_names_are_the_ones_the_pair_writes_and_the_live_mental_status_is_never_among_them():
    assert "mental_status" not in pair.OBSERVABLE_WRITES and pair.OBSERVABLE_WRITES == ("sbp", "dbp", "map")
    assert view.OVERLAY_KEY not in ("observable", "mental_status")
