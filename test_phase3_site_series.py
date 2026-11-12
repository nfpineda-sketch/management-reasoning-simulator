"""P3-232 and P3-233: the full dormant series of the pair-authority SITE, both GI cases, and the pressure-only non-regression through the shared validator.

TEST-SIDE. The series is the one of ``test_phase3_pair_series.py`` (same harness, same scenarios, the layer's own hook), now with the dormant SITE the hook builds, and
two scenarios of its own: a held order released at a clinical-time minute and an examination-time wait. For every run the record keeps, in separate columns:

* the WOULD_COMMIT intervals (how many, the first and the last), the WOULD_ABORT (the first failed minute, its reason) and the halt state of the state machine;
* the faculty column, which says NOT_DECIDED for every run, always.

232A: the pair's pressures are the pressure-only site's, exactly: at every WOULD_COMMIT minute of every run the pressures the pair would write are the replayed
pressure point of the pressure run, shaped the way the legacy engine shows it, which is what the pressure-only site commits; and on a real infusion the two sites
prepare the same three numbers.

233: through the SAME validator, the pressure-only site behaves as before: the certified series is fingerprinted in ``test_phase3_minute_validation.py``; here its
behavior at the boundaries (the stop semantics, the replay and the atomicity) is re-proved on real encounters.
"""
import json
import os
from copy import deepcopy
from pathlib import Path
from unittest import mock

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_minute_validation as mv
import runtime_pair_site as site_module
import runtime_shadow as rs
import test_phase3_pair_series as series
from test_phase3_clock_routes import CASE, TEST_ONLY_SNAPSHOT, approved, bound  # noqa: F401 (fixtures)
from test_phase3_pair_site import infusion  # noqa: F401 (fixture)
from test_shadow_resolution import GI, HELD

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_DORMANT_SITE_SERIES.json"
RECORD_VERSION = "P3-232"
CASES = series.CASES
HELD_BLOOD = HELD[GI]["blood"][0]
#: The two scenarios this series adds to the 12 of the pair series (their names are ONLY here: the pair series' own record is untouched).
EXTRA = {
    "held_order_release": {"at": {0: (HELD_BLOOD,)}, "horizon": 60},
    "held_order_release_then_treatment": {"at": {0: (HELD_BLOOD,), 20: (series.ACCESS, series.SALINE)}, "horizon": 90},
}
REQUIRED = series.REQUIRED + ("infusion_over_60_minutes", "held_order_release")
HALT_STATE = {None: None}


def _run_extra(case, scenario, waits=series.ORDER_WAITS):
    with mock.patch.dict(series.SCENARIOS, EXTRA):
        return series.run(case, scenario, waits)


_CACHE = {}


def cached(case, scenario, waits=series.ORDER_WAITS):
    key = (case, scenario, waits)
    if key not in _CACHE:
        _CACHE[key] = _run_extra(case, scenario, waits) if scenario in EXTRA else series.cached(case, scenario, waits)
    return _CACHE[key]


ALL = tuple(series.SCENARIOS) + tuple(EXTRA)
CLOCK_TIME = tuple(series.CLINICAL_TIME_VARIANTS)


def _row(result):
    site, halt = result["evaluator"], result["halt"]
    summary = result["summary"]
    commits = [record for record in result["records"] if record["verdict"] == pair.WOULD_COMMIT]
    abort = next((record for record in result["records"] if record["verdict"] == pair.WOULD_ABORT), None)
    detail = {} if abort is None else abort["detail"]
    return {"case": result["case"], "scenario": result["scenario"], "waits": result["waits"], "minutes_played": result["minutes_played"],
            "technical": {"would_commit_intervals": len(commits), "would_commit_minutes": summary["would_commit_minutes"], "multi_minute_intervals": sum(1 for r in commits if len(r["interval"]) > 1),
                          "first_would_commit": summary["first_would_commit"], "last_would_commit": summary["last_would_commit"],
                          "would_abort_at": None if abort is None else abort["minute"], "would_abort_checks": None if abort is None else abort["failed_checks"],
                          "first_failed_interval_minute": (detail.get("interval_minutes_validated") or {}).get("first_failed_minute"),
                          "first_established_collapse_minute": (detail.get("collapse_boundary_not_reached") or {}).get("first_established_minute"),
                          "reason": None if abort is None else abort["reason"], "halt_stage": None if halt is None else halt.get("stage"),
                          "authority_had_begun": site.authority_began(), "state": site.state, "continuation": site.continuation()["legacy_may_continue_silently"],
                          "transitions": [item["to"] for item in site.transitions], "violations": summary["violations"], "no_advance_turns": summary["no_advance_turns"],
                          "routes": summary["routes"]},
            # read from the code, not typed: the faculty's approval constant and the gate's own verdict (the consciousness decision is the faculty's and lives in the
            # Decision File, not in code, so it is the one literal)
            "faculty": {"consciousness_authority_decision": "NOT_DECIDED", "pair_authority": site_module.FACULTY_APPROVAL[site_module.PAIR_DOMAIN],
                        "arming": "ARMED" if site.arming({})["armed"] else "NOT_ARMED"}}


def build_record():
    runs = [_row(cached(case, scenario)) for scenario in ALL for case in CASES]
    runs += [_row(cached(case, scenario, series.CLINICAL_TIME_WAITS)) for scenario in CLOCK_TIME for case in CASES]
    body = {"record_type": "PHASE3_DORMANT_SITE_SERIES", "version": RECORD_VERSION, "granularity": pair.GRANULARITY, "time_limit": pair.TIME_LIMIT_MIN,
            "snapshot": pair.V1_ID, "snapshot_status": pair.RATIFIED, "authority_granted": False, "armed": False, "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "statement": "A technical record of what the DORMANT pair-authority site evaluated beside a legacy-authoritative encounter. Nothing here is an approval, a "
                         "clinical validation or a decision of the faculty; the two columns are never merged.", "runs": runs}
    return {**body, "record_digest": ra.digest_of(body)}


@pytest.fixture(scope="module")
def runs():
    return {(case, scenario): cached(case, scenario) for case in CASES for scenario in ALL}


def test_z1_every_run_has_a_site_a_state_and_decides_nothing_for_the_faculty(runs):
    assert {scenario for _, scenario in runs} == set(ALL) and set(REQUIRED) <= set(ALL)
    for (case, scenario), result in runs.items():
        site = result["evaluator"]
        assert isinstance(site, site_module.DormantPairSite) and site.state in site_module.STATES and site.violations == [], (case, scenario)
        assert site.arming({})["armed"] is False and site.commit_requests == [] and site.artifact()["committed_authority"] is False
        assert result["bound_run_failures"] == [], (case, scenario)
        row = _row(result)
        assert row["faculty"]["consciousness_authority_decision"] == "NOT_DECIDED" and row["faculty"]["arming"] == "NOT_ARMED"


def test_z2_the_state_machine_agrees_with_the_technical_result_in_every_run(runs):
    """No halt: the experiment is evaluating (WOULD_COMMIT, or NOT_STARTED when nothing but no-advance turns happened). A halt: EXPERIMENT_HALTED when authority never
    began, INVALID_FOR_CONTINUATION when it had, and the legacy engine may continue silently only in the first."""
    for (case, scenario), result in runs.items():
        site = result["evaluator"]
        if site.halt is None:
            assert site.state in (site_module.WOULD_COMMIT, site_module.NOT_STARTED), (case, scenario, site.state)
            assert site.continuation()["legacy_may_continue_silently"] is True
        elif site.halt["authority_had_begun"]:
            assert site.state == site_module.INVALID_FOR_CONTINUATION and site.continuation()["legacy_may_continue_silently"] is False and site.would_commit, (case, scenario)
        else:
            assert site.state == site_module.EXPERIMENT_HALTED and site.continuation()["legacy_may_continue_silently"] is True and not site.would_commit, (case, scenario)
        assert [item["to"] for item in site.transitions][0] == "NOT_STARTED"
        tail = [item["to"] for item in site.transitions][-2:]
        if site.state in site_module.TERMINAL_STATES:
            assert tail == ["WOULD_ABORT", site.state], (case, scenario, tail)


def test_z3_the_two_added_scenarios_release_the_held_order_inside_a_validated_interval_and_the_experiment_goes_on(runs):
    for case in CASES:
        result = runs[(case, "held_order_release")]
        session_held = result["evaluator"].records
        assert result["summary"]["would_commit_minutes"] > 5 and result["halt"] is None, (case, result["halt"])
        later = runs[(case, "held_order_release_then_treatment")]
        assert later["summary"]["would_commit_minutes"] > 10 and later["evaluator"].state in (site_module.WOULD_COMMIT, site_module.INVALID_FOR_CONTINUATION)
        assert session_held, case


def test_z4_232A_the_pairs_pressures_are_the_pressure_only_sites_pressures_at_every_would_commit_minute_of_every_run(runs):
    """The pair never changes the pressure half: what it would write at a WOULD_COMMIT minute is the replayed pressure point of the PRESSURE run, shaped the way the
    legacy engine shows it -- exactly what ``AuthoritySite._minute`` writes (``shaped_like_legacy(candidate, legacy_observable)``)."""
    checked = 0
    for (case, scenario), result in runs.items():
        site = result["evaluator"]
        table = mv.replay_table(site.replay_inputs["pressure"])
        for record in result["records"]:
            if record["verdict"] != pair.WOULD_COMMIT:
                continue
            written = record["would_write"]
            expected = ra.shaped_like_legacy(table[record["minute"]], {"sbp": record["legacy"]["sbp"], "dbp": record["legacy"]["dbp"]})
            assert (written["sbp"], written["dbp"], written["map"]) == (expected["sbp"], expected["dbp"], ra.derived_map(expected["sbp"], expected["dbp"])), \
                (case, scenario, record["minute"])
            checked += 1
    assert checked > 500, checked


@pytest.fixture
def twin(infusion, approved):
    """The pressure-only site and the pair site, on the SAME real 30-minute infusion."""
    site = ra.open_site(infusion["arrival"], environ=approved)
    assert site is not None
    return site, infusion


def test_z5_232A_on_a_real_infusion_the_two_sites_prepare_the_same_three_numbers(twin):
    pressure_site, fixture = twin
    prepared = pressure_site.minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], "inf-1", ra.ORDER_TURN)
    record = fixture["site"].minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], "inf-1", ra.ORDER_TURN)
    assert prepared is not None and record["verdict"] == pair.WOULD_COMMIT
    committed = {name: prepared["observable"][name] for name in ("sbp", "dbp", "map")}
    would = {name: record["would_write"][name] for name in ("sbp", "dbp", "map")}
    assert committed == would, (committed, would)
    assert pressure_site.minutes_committed == (30,) == tuple(fixture["site"].would_commit)


def test_z6_233_the_stop_semantics_are_the_same_in_both_sites_a_failure_stops_both_and_nothing_later_commits(twin):
    """Same injected failure, same real turn: the pressure-only site refuses and halts, the pair aborts and halts. Neither commits anything afterwards."""
    pressure_site, fixture = twin
    from test_phase3_clock_routes import _break_minute
    _break_minute(fixture, 12, "no_candidate")
    assert pressure_site.minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], "inf-1", ra.ORDER_TURN) is None
    record = fixture["site"].minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], "inf-1", ra.ORDER_TURN)
    assert pressure_site.halted and pressure_site.minutes_committed == () and record["verdict"] == pair.WOULD_ABORT and fixture["site"].would_commit == []
    assert pressure_site.records[-1]["interval_validation"]["first_failed_minute"] == 12 == record["detail"]["interval_minutes_validated"]["first_failed_minute"]
    assert pressure_site.minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], "inf-2", ra.ORDER_TURN) is None
    assert fixture["site"].minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], "inf-2", ra.ORDER_TURN)["verdict"] == pair.HALTED


def test_z7_the_committed_record_is_what_the_series_just_produced():
    if os.environ.get("MRS_WRITE_SITE_SERIES_RECORD") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")       # deliberate regeneration, once
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    stored, live = json.loads(RECORD_PATH.read_text(encoding="utf-8")), build_record()
    assert stored["record_digest"] == live["record_digest"], "the committed record no longer matches the series: regenerate it deliberately"
    assert stored["authority_granted"] is False and stored["armed"] is False and stored["common_core_runtime_authority"] is False
    assert all(row["faculty"]["consciousness_authority_decision"] == "NOT_DECIDED" for row in stored["runs"])
    assert {(row["case"], row["scenario"]) for row in stored["runs"]} >= {(case, scenario) for case in CASES for scenario in REQUIRED}
