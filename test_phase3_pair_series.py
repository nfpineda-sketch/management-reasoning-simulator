"""P3-218: the full dry series, run with the LAYER's own hook and evaluator, on both GI cases, at the granularity of the actual transaction.

TEST-SIDE. Nothing here enables an authority, sets an authority flag, opens an authority site or writes into an encounter. The legacy engine is the only
authority of every encounter below. What runs beside it is ``runtime_authority_pair.after_clock_moved`` -- the SAME function the page calls -- and the
dry evaluator it opens: it says, for every turn that moves the clock, whether the pressure + consciousness pair WOULD commit, WOULD abort, or is already
HALTED. It never writes.

Two columns that must never be merged are kept apart in every row of the record (P3-218A):

* ``technical``: what the dry evaluator reproduced (a transaction that completed, a window, a boundary, a refusal and its name);
* ``faculty``: whether the faculty decided anything about consciousness authority. It did not: the column says ``NOT_DECIDED`` for every run, always.

Both columns exist so that a technically clean series is never read as an approval, and an approval is never read off a technical series.
"""
import json
import os
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_gi_amendment_2_series as series
from family_engine import advance_clinical_time

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_PAIR_DRY_SERIES.json"
RECORD_VERSION = "P3-218"
CASES = ("gi_bleed_57m", "gi_bleed_72f")
ACCESS, SALINE, BLOOD, BLOOD_MORE = series.ACCESS, series.SALINE, series.BLOOD, series.BLOOD_MORE
UNSUPPORTED = "Start norepinephrine at 10 mcg/min."
INFUSION = "Give 1000 mL normal saline over 60 minutes."
#: The scenarios the assignment names, then the extras. ``trigger`` is read on the BOUND run's own category, never on a witness name.
SCENARIOS = {
    "untreated": {"at": {}, "horizon": 240},
    "early_treatment": {"at": {10: (ACCESS, SALINE, BLOOD)}, "horizon": 120},
    "delayed_treatment": {"at": {120: (ACCESS, SALINE, BLOOD)}, "horizon": 200},
    "fluid_only": {"at": {10: (ACCESS, SALINE), 40: (SALINE,)}, "horizon": 120},
    "blood_only": {"at": {10: (ACCESS, BLOOD)}, "horizon": 120},
    "severe_deterioration": {"at": {}, "horizon": 240, "trigger": (2, (ACCESS, SALINE))},
    "recovery_after_severe": {"at": {}, "horizon": 240, "trigger": (3, (ACCESS, SALINE, BLOOD_MORE)), "after": 45},
    "late_rescue": {"at": {215: (ACCESS, SALINE, BLOOD_MORE)}, "horizon": 300},
    "iv_line_scenario": {"at": {0: (ACCESS,), 10: (SALINE, BLOOD)}, "horizon": 120},
    "unsupported_action_scenario": {"at": {10: (UNSUPPORTED,)}, "horizon": 80},
    # extras: a recovery whose infusion ends inside the window; a 60-minute infusion in ONE turn
    "recovery_within_window": {"at": {}, "horizon": 240, "trigger": (3, (ACCESS, SALINE, BLOOD))},
    "infusion_over_60_minutes": {"at": {10: (INFUSION,)}, "horizon": 120},
}
REQUIRED = ("untreated", "early_treatment", "delayed_treatment", "fluid_only", "blood_only", "severe_deterioration", "recovery_after_severe", "late_rescue",
            "iv_line_scenario", "unsupported_action_scenario")
#: How the resident lets time pass between orders: an order turn ("Reassess in 1 minutes") or clinical time outside an order turn (a question).
ORDER_WAITS, CLINICAL_TIME_WAITS = "order_turn_waits", "clinical_time_waits"
CLINICAL_TIME_VARIANTS = ("untreated", "early_treatment", "iv_line_scenario", "unsupported_action_scenario")
#: The size of one resident turn that only lets time pass. Five minutes is a turn a resident really gives ("Reassess in 5 minutes"); a history question costs
#: two (``clinical_time.ACTIVE_MINUTES``). The evaluator validates EVERY minute inside a turn, so a larger turn is not a coarser check -- and a one-minute turn
#: would replay the common core once per minute (a run of 240 minutes took ~4.5 minutes of CPU), which is cost, not safety.
STEP_ORDERS, STEP_TIME = 5, 2


@contextmanager
def observing(stores):
    """Call the layer's hook where the page calls it: right after the shadow observed a turn, and after the order's fate was settled. The patch is the existing
    development harness's own technique; unlike an authority harness, NOTHING is written back to the state."""
    real_observe, real_order = rs.ShadowSession.observe, acceptance.Encounter.order
    if getattr(real_observe, "_pair_series_patch", False):
        raise RuntimeError("the series is already observing: a nested observer would evaluate every turn twice")

    def observe(self, before, state, parsed=None, result=None, ran=None, submission_id=None):
        real_observe(self, before, state, parsed, result, ran, submission_id)
        held = stores.get(id(self))
        if held is not None:
            pair.after_clock_moved(held, self, before, state, ran, submission_id, ra.ORDER_TURN)

    def order(self, text):
        entry = real_order(self, text)
        shadow = getattr(self, "shadow", None)
        held = stores.get(id(shadow))
        if held is not None:
            pair.after_orders_settled(held, shadow, entry.get("orders") if isinstance(entry, dict) else None)
        return entry
    observe._pair_series_patch = True
    rs.ShadowSession.observe, acceptance.Encounter.order = observe, order
    try:
        yield
    finally:
        rs.ShadowSession.observe, acceptance.Encounter.order = real_observe, real_order


def _spend(encounter, minutes, stores):
    """The page's ``spend_clinical_time``, for the engine, the shadow and the hook: capture, let the time pass, observe it, call the ONE hook."""
    before = encounter.shadow.capture(encounter.state)
    result = advance_clinical_time(encounter.state, minutes, label="history_question")
    encounter.shadow.observe_time(before, encounter.state, result)
    pair.after_clock_moved(stores[id(encounter.shadow)], encounter.shadow, before, encounter.state, None, None, ra.CLINICAL_TIME)


def run(case, scenario, waits=ORDER_WAITS):
    """One legacy-authoritative encounter with the layer's dry evaluator beside it, through the hook."""
    plan = SCENARIOS[scenario]
    stores, orders = {}, []
    previous = {name: os.environ.get(name) for name in (pair.DRY_FLAG,)}
    os.environ[pair.DRY_FLAG] = pair.DRY_ON
    try:
        with ev.shadow(rs.MODE_SHADOW_COMPARE), observing(stores):
            encounter = acceptance.Encounter(case)
            stores[id(encounter.shadow)] = held = {}
            fired, triggered, stop_after = set(), None, None
            while int(encounter.minute) < plan["horizon"]:
                due = []
                for minute in sorted(plan["at"]):
                    if minute <= int(encounter.minute) and minute not in fired:
                        fired.add(minute)
                        due.extend(plan["at"][minute])
                evaluator = None if pair.DRY_KEY not in held else held[pair.DRY_KEY][1]
                trigger = plan.get("trigger")
                if triggered is None and trigger is not None and evaluator is not None and evaluator.records:
                    shown = evaluator.records[-1]["common"]
                    if shown is not None and shown["category"] is not None and shown["category"] >= trigger[0]:
                        triggered, due = int(encounter.minute), list(trigger[1])
                        stop_after = triggered + plan["after"] if plan.get("after") else None
                if due:
                    started, text = int(encounter.minute), " ".join(due)
                    entry = encounter.order(text)
                    orders.append({"minute": started, "text": text, "executed": bool(entry["executed"]), "clock_after": int(encounter.minute)})
                if encounter.arrested or (stop_after is not None and int(encounter.minute) >= stop_after):
                    break
                before = int(encounter.minute)
                if waits == CLINICAL_TIME_WAITS:
                    _spend(encounter, STEP_TIME, stores)
                else:
                    encounter.wait_until(before + STEP_ORDERS, step=STEP_ORDERS)
                if int(encounter.minute) == before:
                    break
            final = dict(encounter.state.get("observable") or {})
            session = encounter.shadow
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    held_pair = held.get(pair.DRY_KEY)
    evaluator = None if held_pair is None else held_pair[1]
    assert evaluator is not None, (case, scenario, held.get(pair.DRY_REFUSAL_KEY))
    return {"case": case, "scenario": scenario, "waits": waits, "orders": orders, "triggered_at": triggered, "minutes_played": int(encounter.minute),
            "legacy_arrested": bool(encounter.arrested), "evaluator": evaluator, "summary": evaluator.summary(), "records": evaluator.records, "halt": evaluator.halt,
            "final": {key: final.get(key) for key in ("sbp", "dbp", "mental_status", "pulse_present")}, "session_failures": len(session.failures),
            "bound_run_failures": [f"{item.minute}:{item.where}:{item.exception}" for item in (evaluator.runner.failures if evaluator.runner else [])]}


def legacy_alone(case, scenario, waits=ORDER_WAITS):
    """The same orders at the same minutes with the shadow OFF and no evaluator: the legacy trajectory nobody observed."""
    plan = SCENARIOS[scenario]
    track = []
    with ev.shadow(rs.MODE_OFF):
        encounter = acceptance.Encounter(case)
        fired = set()
        while int(encounter.minute) < plan["horizon"]:
            due = []
            for minute in sorted(plan["at"]):
                if minute <= int(encounter.minute) and minute not in fired and plan.get("trigger") is None:
                    fired.add(minute)
                    due.extend(plan["at"][minute])
            if due:
                encounter.order(" ".join(due))
            if encounter.arrested:
                break
            before = int(encounter.minute)
            if waits == CLINICAL_TIME_WAITS:
                advance_clinical_time(encounter.state, STEP_TIME, label="history_question")
            else:
                encounter.wait_until(before + STEP_ORDERS, step=STEP_ORDERS)
            if int(encounter.minute) == before:
                break
            observable = encounter.state.get("observable") or {}
            track.append((int(encounter.minute), observable.get("sbp"), observable.get("dbp"), observable.get("mental_status")))
    return track


_CACHE = {}


def cached(case, scenario, waits=ORDER_WAITS):
    key = (case, scenario, waits)
    if key not in _CACHE:
        _CACHE[key] = run(case, scenario, waits)
    return _CACHE[key]


VERDICT_CODE = {pair.WOULD_COMMIT: "W", pair.WOULD_ABORT: "A", pair.HALTED: "H", pair.NO_ADVANCE: "N"}


def compact(result):
    """A run for the record: the technical result and, in its own column, the faculty's (absent) decision."""
    summary, halt = result["summary"], result["halt"]
    rows = [[item["minute"], item["route"][:5], VERDICT_CODE[item["verdict"]], len(item["interval"]), ",".join(item["failed_checks"])]
            for item in result["records"] if item["verdict"] != pair.WOULD_COMMIT or len(item["interval"]) > 1]
    return {"case": result["case"], "scenario": result["scenario"], "waits": result["waits"], "orders": result["orders"], "triggered_at": result["triggered_at"],
            "minutes_played": result["minutes_played"], "legacy_arrested": result["legacy_arrested"],
            "technical": {"verdict": "WOULD_ABORT" if halt is not None else "WOULD_COMMIT_THROUGHOUT",
                          "would_commit_minutes": summary["would_commit_minutes"], "first_would_commit": summary["first_would_commit"],
                          "last_would_commit": summary["last_would_commit"], "no_advance_turns": summary["no_advance_turns"],
                          "first_would_abort": summary["first_would_abort"], "abort_checks": summary["abort_checks"], "abort_stage": summary["abort_stage"],
                          "authority_had_begun_at_abort": summary["authority_had_begun_at_abort"], "halted_minutes": summary["halted_minutes"],
                          # WHERE inside the aborting turn the check failed (a turn ends at its last minute; the boundary or the failed minute may lie before it)
                          "abort_detail": None if halt is None else json.loads(json.dumps(halt.get("detail") or {}, default=str)),
                          "routes": summary["routes"], "record_digest": summary["record_digest"], "violations": summary["violations"]},
            "faculty": {"consciousness_authority_decision": "NOT_DECIDED", "pressure_authority": "READY_IN_DEVELOPMENT_HARNESS_ONLY_NOT_PAGE_RUNTIME"},
            "multi_minute_or_non_commit_turns": rows, "final_legacy": result["final"]}


def build_record():
    runs = [compact(cached(case, scenario)) for scenario in SCENARIOS for case in CASES]
    runs += [compact(cached(case, scenario, CLINICAL_TIME_WAITS)) for scenario in CLINICAL_TIME_VARIANTS for case in CASES]
    body = {"record_type": "PHASE3_PAIR_DRY_SERIES", "version": RECORD_VERSION, "granularity": pair.GRANULARITY, "time_limit": pair.TIME_LIMIT_MIN,
            "snapshot": pair.V1_ID, "authority_granted": False, "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "statement": "A technical record of what a dry pair transaction would have done beside a legacy-authoritative encounter. Nothing here is an approval, a "
                         "clinical validation or a decision of the faculty; the two columns are never merged.",
            "runs": runs}
    return {**body, "record_digest": ra.digest_of(body)}


def write_record():
    record = build_record()
    RECORD_PATH.write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")
    return record


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# claims, each proved on the real series
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def everything():
    return {(case, scenario): cached(case, scenario) for case in CASES for scenario in SCENARIOS}


def test_series_1_every_run_is_clean_on_the_technical_side_and_decides_nothing_for_the_faculty(everything):
    assert set(everything) == {(case, scenario) for case in CASES for scenario in SCENARIOS} and set(REQUIRED) <= set(SCENARIOS)
    for (case, scenario), result in everything.items():
        assert result["summary"]["violations"] == [] and result["bound_run_failures"] == [], (case, scenario)
        assert result["summary"]["snapshot_is_the_pinned_version_1"] is True and result["summary"]["granularity"] == pair.VALIDATED_ATOMIC_INTERVAL
        assert all(row["route"] in ra.KNOWN_ROUTES for row in result["records"]), (case, scenario)
        # the record never mixes the two columns
        row = compact(result)
        assert row["faculty"]["consciousness_authority_decision"] == "NOT_DECIDED" and row["technical"]["violations"] == []


def test_series_2_no_run_ever_has_a_would_commit_after_its_first_abort(everything):
    for (case, scenario), result in everything.items():
        records = result["records"]
        aborts = [index for index, row in enumerate(records) if row["verdict"] == pair.WOULD_ABORT]
        assert len(aborts) <= 1, (case, scenario)
        if aborts:
            tail = records[aborts[0] + 1:]
            assert all(row["verdict"] == pair.HALTED for row in tail), (case, scenario, [row["verdict"] for row in tail][:5])
            assert result["summary"]["would_commit_minutes"] == len([row for row in records[:aborts[0]] if row["verdict"] == pair.WOULD_COMMIT])


def test_series_3_the_untreated_course_commits_until_the_window_or_the_collapse_boundary_ends_it_and_says_which(everything):
    for case in CASES:
        result = everything[(case, "untreated")]
        summary = result["summary"]
        assert summary["would_commit_minutes"] > 20 and summary["first_would_commit"] == STEP_ORDERS, (case, summary)
        assert summary["abort_checks"] and set(summary["abort_checks"]) <= {"window_open", "collapse_boundary_not_reached", "interval_minutes_validated",
                                                                           "pressure_validated", "pair_is_one_course"}, (case, summary["abort_checks"])
        assert summary["last_would_commit"] < summary["first_would_abort"] <= pair.TIME_LIMIT_MIN + 1


def test_series_4_the_iv_line_is_executed_without_physiology_and_the_experiment_goes_on(everything):
    for case in CASES:
        result = everything[(case, "iv_line_scenario")]
        iv = [row for row in result["records"] if row["no_common_physiology"]]
        assert iv, case
        assert iv[0]["verdict"] == pair.NO_ADVANCE and iv[0]["minute"] == 0 and iv[0]["no_common_physiology"][0]["disposition"] == ra.EXECUTED_NO_COMMON_PHYSIOLOGY
        assert result["halt"] is None or "supported_management" not in result["halt"]["failed_checks"], (case, result["halt"])
        assert result["summary"]["no_advance_turns"] >= 1 and result["summary"]["would_commit_minutes"] > 10
        assert [row for row in result["records"] if row["minute"] > 10 and row["verdict"] == pair.WOULD_COMMIT]
        # and the treatment bundles of the other scenarios carry an IV line inside one turn without stopping it
        early = everything[(case, "early_treatment")]
        assert any(row["no_common_physiology"] and row["verdict"] == pair.WOULD_COMMIT for row in early["records"]), case


def test_series_5_the_unsupported_action_is_a_would_abort_at_its_own_turn_with_authority_having_begun(everything):
    for case in CASES:
        result = everything[(case, "unsupported_action_scenario")]
        halt = result["halt"]
        assert halt is not None and "supported_management" in halt["failed_checks"] and halt["authority_had_begun"] is True, (case, halt)
        assert result["summary"]["first_would_abort"] >= 10 and result["summary"]["last_would_commit"] < result["summary"]["first_would_abort"]
        assert "INVALID_FOR_CONTINUATION" in halt["consequence"]


def test_series_6_a_sixty_minute_infusion_is_one_turn_validated_at_each_of_its_minutes(everything):
    for case in CASES:
        result = everything[(case, "infusion_over_60_minutes")]
        long_turns = [row for row in result["records"] if len(row["interval"]) >= 60]
        assert long_turns, case
        turn = long_turns[0]
        assert turn["verdict"] == pair.WOULD_COMMIT and all(item["ok"] for item in turn["interval"]), (case, turn["failed_checks"])
        assert [item["minute"] for item in turn["interval"]] == list(range(turn["minute"] - len(turn["interval"]) + 1, turn["minute"] + 1))


def test_series_7_the_treated_courses_commit_through_their_horizon_or_say_why_not(everything):
    for case in CASES:
        for scenario in ("early_treatment", "fluid_only", "blood_only", "recovery_after_severe", "recovery_within_window", "delayed_treatment"):
            result = everything[(case, scenario)]
            summary = result["summary"]
            assert summary["would_commit_minutes"] > 0, (case, scenario)
            if summary["first_would_abort"] is not None:
                assert summary["abort_checks"], (case, scenario)


def test_series_8_the_clinical_time_route_gives_the_same_dry_course_as_waiting_by_order_turns():
    """Waiting by questions (clinical time outside an order turn) is evaluated too, and the engine's pressure course is the legacy course either way."""
    for case in CASES:
        for scenario in ("untreated", "early_treatment"):
            by_orders, by_time = cached(case, scenario), cached(case, scenario, CLINICAL_TIME_WAITS)
            assert ra.CLINICAL_TIME in by_time["summary"]["routes"], (case, scenario)
            assert by_time["summary"]["violations"] == [] and by_time["bound_run_failures"] == []
            assert by_time["summary"]["would_commit_minutes"] > 20, (case, scenario)
            # the two ways of letting a minute pass give the SAME course (the engine does not care which route moved its clock): at every minute both
            # evaluated, the common core's own category is the same
            a = {row["minute"]: row["common"]["category"] for row in by_orders["records"] if row["common"] and row["verdict"] == pair.WOULD_COMMIT}
            b = {row["minute"]: row["common"]["category"] for row in by_time["records"] if row["common"] and row["verdict"] == pair.WOULD_COMMIT}
            overlap = [minute for minute in a if minute in b]
            assert len(overlap) >= 5, (case, scenario)                   # the turns end at different minutes on the two routes; the minutes both evaluated must agree
            assert all(a[minute] == b[minute] for minute in overlap), (case, scenario, [m for m in overlap if a[m] != b[m]][:5])


def test_series_9_observing_changes_nothing_the_legacy_engine_does():
    """The legacy trajectory with the hook and the evaluator beside it is exactly the trajectory of the same orders nobody observed."""
    for case in CASES:
        for scenario in ("untreated", "early_treatment", "iv_line_scenario"):
            observed = cached(case, scenario)
            alone = legacy_alone(case, scenario)
            assert alone, (case, scenario)
            final_alone = alone[-1]
            assert (observed["final"]["sbp"], observed["final"]["dbp"], observed["final"]["mental_status"]) == final_alone[1:], (case, scenario)
            assert observed["minutes_played"] == final_alone[0]


def test_series_10_the_committed_record_is_what_the_series_just_produced():
    if os.environ.get("MRS_WRITE_PAIR_SERIES_RECORD") == "1":
        write_record()                                           # deliberate regeneration, once, by the person who changes the series
    assert RECORD_PATH.exists(), "the record is produced once by write_record() and committed"
    stored = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    live = build_record()
    assert stored["record_digest"] == live["record_digest"], "the committed series record no longer matches the series: regenerate it deliberately"
    assert stored["authority_granted"] is False and stored["common_core_runtime_authority"] is False
    assert {(row["case"], row["scenario"]) for row in stored["runs"]} >= {(case, scenario) for case in CASES for scenario in REQUIRED}
    assert all(row["faculty"]["consciousness_authority_decision"] == "NOT_DECIDED" for row in stored["runs"])
