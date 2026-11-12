"""P3-222 and P3-223: ONE per-minute validation primitive, and the repair of the pressure-only site's R2.

TEST-SIDE. Nothing here enables an authority: every commit below is made on a copy through the test-only approval pattern of the P3-28 certification.

* P3-222: ``runtime_minute_validation`` is the only place a minute's pressure is judged valid. The pair evaluator and the pressure-only site call it; the two modes
  differ in one thing (whether the consciousness half is judged); the pressure-only mode refuses a consciousness candidate.
* P3-223 (R2): the pressure-only site used to validate only the minute it committed. A turn that crossed N minutes committed the END state even when an
  intermediate minute had no candidate or one the artifact does not reproduce. It now validates every minute. The certified pressure series (both GI cases)
  is fingerprinted: 34 scenarios, 26 complete, 8 stopped, 66 committed minutes, 78 minute records, identical before and after the repair.
"""
import ast
import dataclasses
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_minute_validation as mv
import runtime_shadow as rs
import test_runtime_authority_series as series_harness
from test_phase3_clock_routes import CASE, _break_minute, _site, approved, bound, site_infusion  # noqa: F401 (fixtures)

ROOT = Path(__file__).resolve().parent
#: Taken over (case, scenario, halted, halt_reason, committed, minutes, [minute, outcome, common_pressures, failure_reason]) of the P3-48 series, both cases,
#: BEFORE the R2 repair and AFTER it: the same digest.
SERIES_FINGERPRINT = "41ad69758c782926e29f32a6f163abc3150271ac85bd77d23dc05d9debd297a5"
#: P3-245 (declared adaptation): the real experiment now stops BEFORE a collapse boundary the V1 overlay reads (FD-AUTH-06/17). The certified series above is reproduced EXACTLY
#: with that guard neutralized (``SERIES_FINGERPRINT``), and with the guard in force ONLY the two ``terminal_deterioration`` scenarios change: 8 commits become 6 (the last commit is
#: minute 180; established collapse is read at minute 207) and they stop with ``COLLAPSE_BOUNDARY_REACHED`` instead of completing: 24 completed, 10 stopped, 62 committed minutes,
#: the same 78 minute records, and this fingerprint. The other 32 scenarios keep their rows bit for bit (``NON_TERMINAL_FINGERPRINT`` is equal in both runs).
SERIES_FINGERPRINT_WITH_THE_BOUNDARY = "162517318417f2c9d3376d86a2e675867fc3a5cf6a09132716bd8f8c0a9137b5"


# -- P3-222: the primitive -------------------------------------------------------------------------------------------------------------------------------

def test_m1_the_two_modes_are_named_and_an_unknown_one_is_refused():
    assert mv.MODES == (mv.PRESSURE_ONLY, mv.PAIR_PRESSURE_CONSCIOUSNESS) == ("PRESSURE_ONLY", "PAIR_PRESSURE_CONSCIOUSNESS")
    assert mv.judges_consciousness(mv.PAIR_PRESSURE_CONSCIOUSNESS) is True and mv.judges_consciousness(mv.PRESSURE_ONLY) is False
    with pytest.raises(mv.ModeError):
        mv.judges_consciousness("PAIR")
    with pytest.raises(mv.ModeError):
        mv.validate_interval([1], mode="whatever", case_id=CASE, snapshot=None, session=None, unsupported=(), legacy_arrest=False, table=None)


def test_m2_the_pressure_only_mode_cannot_be_handed_a_consciousness_candidate_so_it_can_never_make_it_authoritative(site_infusion):
    """FD-AUTH-16 / 222B. Handing the pressure-only validation the bound run's results or its channels is an error, not a silent ignore."""
    session = site_infusion["session"]
    common = dict(case_id=CASE, snapshot=ra.approved_snapshot("gi_pressure_committed", environment="development", family=ra.AUTHORITY_FAMILY, case_id=CASE,
                                                              domain=ra.AUTHORITY_DOMAIN), session=session, unsupported=(), legacy_arrest=False, table=None)
    with pytest.raises(mv.ModeError):
        mv.validate_interval([1, 2], mode=mv.PRESSURE_ONLY, bound_results=list(session.runner.results), **common)
    with pytest.raises(mv.ModeError):
        mv.validate_interval([1, 2], mode=mv.PRESSURE_ONLY, channel_rows={1: {"channels": {}}}, **common)
    rows = mv.validate_interval([1, 2], mode=mv.PRESSURE_ONLY, **common)
    names = {name for row in rows["rows"] for name in row["failed"]}
    assert not names & {mv.CONSCIOUSNESS_CANDIDATE_PRESENT, mv.PULSE_PRESENT, mv.PAIR_IS_ONE_COURSE}, names


def _function_source(path: str, owner: str, name: str) -> str:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == owner):
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return ast.unparse(node)
    raise AssertionError((path, owner, name))


def test_m3_neither_the_pair_evaluator_nor_the_pressure_site_judges_a_minute_by_itself_they_both_call_the_primitive():
    """222A. The per-minute loop is not duplicated: no ``AuthorityTransaction`` is opened in either caller's interval functions, and both name the one primitive."""
    for path, owner, name in (("runtime_authority.py", "AuthoritySite", "_interval_check"), ("runtime_authority_pair.py", "PairDryEvaluator", "validate_interval"),
                              ("runtime_authority_pair.py", "PairDryEvaluator", "_interval")):
        source = _function_source(path, owner, name)
        assert "AuthorityTransaction(" not in source and ".validate(" not in source.replace("validate_interval(", ""), (owner, name)
    assert "validation.validate_interval(" in _function_source("runtime_authority.py", "AuthoritySite", "_interval_check")
    assert "mv.validate_interval(" in _function_source("runtime_authority_pair.py", "PairDryEvaluator", "validate_interval")
    assert "mv.replay_table(" in _function_source("runtime_authority_pair.py", "PairDryEvaluator", "_replay_table")
    # the primitive itself opens the per-minute transaction in exactly one place
    text = (ROOT / "runtime_minute_validation.py").read_text(encoding="utf-8")
    assert text.count("ra.AuthorityTransaction(") == 1 and text.count("def pressure_failures(") == 1
    # and the old pair loop is gone
    assert "step.validate(" not in (ROOT / "runtime_authority_pair.py").read_text(encoding="utf-8")


def test_m4_the_pair_pressure_half_is_exactly_the_pressure_only_verdict_on_a_clean_and_on_a_broken_run(site_infusion, bound):
    """232A in miniature: for the SAME session, the pair mode's pressure failures are identical to the pressure-only mode's, minute by minute."""
    session = site_infusion["session"]
    snapshot = ra.approved_snapshot("gi_pressure_committed", environment="development", family=ra.AUTHORITY_FAMILY, case_id=CASE, domain=ra.AUTHORITY_DOMAIN)
    dry = pair.PairDryEvaluator(bound, CASE, site_infusion["arrival"])
    dry.runner.mirror(session.mirrored)
    dry.runner.advance(30, state=session._mapping_state())
    channels = {row["minute"]: row for row in pair.fam.run_channels(dry.runner)}
    table = mv.replay_table(ra.AuthoritySite._artifact_input(session))
    minutes = list(range(1, 31))

    def both():
        common = dict(case_id=CASE, snapshot=snapshot, session=session, unsupported=(), legacy_arrest=False, table=table)
        only = mv.validate_interval(minutes, mode=mv.PRESSURE_ONLY, **common)
        paired = mv.validate_interval(minutes, mode=mv.PAIR_PRESSURE_CONSCIOUSNESS, bound_results=list(dry.runner.results), channel_rows=channels, **common)
        return only, paired
    only, paired = both()
    assert only["ok"] and paired["ok"] and only["first_failed_minute"] is None
    for k, how in ((1, "no_candidate"), (15, "failure_at_minute"), (29, "no_candidate")):
        failures, results = list(session.failures), list(session.runner.results)
        _break_minute({"session": session}, k, how)
        only, paired = both()
        keep = lambda names: [name for name in names if name.startswith("pressure")]            # noqa: E731
        assert [(row["minute"], keep(row["failed"])) for row in only["rows"]] == [(row["minute"], keep(row["failed"])) for row in paired["rows"]]
        assert only["first_failed_minute"] == k and only["ok"] is False and only["ineligible_after"] == list(range(k + 1, 31))
        assert paired["first_failed_minute"] is not None and paired["first_failed_minute"] <= k
        session.failures[:], session.runner.results[:] = failures, results


def test_m5_the_first_failed_minute_makes_every_later_minute_ineligible_whatever_its_own_row_says(site_infusion):
    """228B. A clean final state cannot override a failed intermediate one: the verdict is the conjunction, and the minutes after the first failure are listed."""
    session = site_infusion["session"]
    snapshot = ra.approved_snapshot("gi_pressure_committed", environment="development", family=ra.AUTHORITY_FAMILY, case_id=CASE, domain=ra.AUTHORITY_DOMAIN)
    _break_minute({"session": session}, 10, "no_candidate")
    out = mv.validate_interval(list(range(1, 31)), mode=mv.PRESSURE_ONLY, case_id=CASE, snapshot=snapshot, session=session, unsupported=(), legacy_arrest=False,
                               table=mv.replay_table(ra.AuthoritySite._artifact_input(session)))
    assert out["ok"] is False and out["first_failed_minute"] == 10 and out["ineligible_after"] == list(range(11, 31))
    assert out["rows"][-1]["ok"] is True                                  # the END minute is clean on its own: that is exactly the attack
    assert out["interval_minutes"] == [1, 30]


# -- P3-223: R2 at the pressure-only site ---------------------------------------------------------------------------------------------------------------------

def _turn_at_the_site(site_infusion, approved):
    site = _site(site_infusion["arrival"], approved)
    return site, (site_infusion["before"], deepcopy(site_infusion["after"]), site_infusion["session"], site_infusion["ran"], "inf-1", ra.ORDER_TURN)


def test_r2_negative_control_a_clean_multi_minute_turn_still_commits_once_with_no_interval_note(site_infusion, approved):
    site, args = _turn_at_the_site(site_infusion, approved)
    assert site.minute(*args) is not None and site.minutes_committed == (30,) and not site.halted
    assert "interval_validation" not in site.records[-1]                  # a passing turn leaves the certified record byte for byte as it was


@pytest.mark.parametrize("k", (1, 15, 29))
def test_r2_an_intermediate_minute_with_no_candidate_refuses_the_whole_interval_at_the_early_middle_and_late_minute(site_infusion, approved, k):
    """223B. The END minute (30) is clean; the old site committed it. Now nothing commits, the minute that failed is named, and nothing later can become
    authoritative (the site is halted)."""
    site, args = _turn_at_the_site(site_infusion, approved)
    _break_minute(site_infusion, k, "no_candidate")
    assert site.minute(*args) is None
    assert site.halted and site.minutes_committed == () and ra.VALIDATION_REFUSED in site.halt_reason
    record = site.records[-1]
    assert record["outcome"] == ra.ABORTED and record["committed"] == []
    assert record["interval_validation"]["first_failed_minute"] == k and record["interval_validation"]["mode"] == mv.PRESSURE_ONLY
    assert record["interval_validation"]["ineligible_after"] == list(range(k + 1, 30)), "only the intermediate minutes after k; the end minute is the commit"
    assert "interval_minutes_validated" in record["rollback"]["validation_failures"]
    assert site.minute(*args) is None and site.minutes_committed == ()    # a halted site stays halted: no later turn becomes authoritative


@pytest.mark.parametrize("k", (1, 15, 29))
def test_r2_an_intermediate_minute_the_artifact_does_not_reproduce_refuses_the_interval(site_infusion, approved, monkeypatch, k):
    """The second thing the old site could not see: a minute whose replay disagrees with the shadow's. Drift injected at ONE intermediate minute."""
    site, args = _turn_at_the_site(site_infusion, approved)
    real = mv.replay_table

    def drifted(replay_input):
        table = real(replay_input)
        if table is not None and k in table:
            table[k] = {**table[k], "sbp": float(table[k]["sbp"]) + 3.0}
        return table
    monkeypatch.setattr(mv, "replay_table", drifted)
    assert site.minute(*args) is None and site.halted and site.minutes_committed == ()
    detail = site.records[-1]["interval_validation"]
    assert detail["first_failed_minute"] == k and "pressure:minute_reproducible" in detail["failed"]


def test_r2_a_failure_the_shadow_recorded_at_an_intermediate_minute_keeps_its_old_reason_and_is_not_double_reported(site_infusion, approved):
    """A failure recorded at minute k already refused the END minute (the certified P3-216 behavior); the interval check adds nothing and the reason is unchanged."""
    site, args = _turn_at_the_site(site_infusion, approved)
    site_infusion["session"].failures.append(rs.ShadowFailure(12, "mid_interval", "InjectedFailure", "a failure inside the turn", rs.MAPPING_GAP))
    assert site.minute(*args) is None and site.halted and "interval_validation" not in site.records[-1]


def test_r2_a_problem_of_the_consciousness_side_is_not_the_pressure_only_sites_business(site_infusion, approved):
    """222B: in the pressure-only mode the consciousness is not judged, so a reading that only the pair compares cannot refuse a pressure commit."""
    site, args = _turn_at_the_site(site_infusion, approved)
    session = site_infusion["session"]
    index = next(position for position, item in enumerate(session.runner.results) if int(item.minute) == 15)
    derived = dict(session.runner.results[index].derived)
    name = next(reading for reading in pair.SHARED_READINGS if reading not in ("sbp", "dbp", "map") and isinstance(derived.get(reading), (int, float))
                and not isinstance(derived.get(reading), bool))
    derived[name] = float(derived[name]) + 7.0                          # a reading that is NOT in the pressure domain: only the pair's one-course check reads it
    session.runner.results[index] = dataclasses.replace(session.runner.results[index], derived=derived)
    assert site.minute(*args) is not None and site.minutes_committed == (30,)


def test_r2_a_transaction_that_passed_its_own_minute_can_be_refused_for_the_interval_and_can_never_commit_afterwards(site_infusion, approved):
    transaction = ra.AuthorityTransaction(minute=3, case_id=CASE, snapshot=ra.approved_snapshot("gi_pressure_committed", environment="development", family=ra.AUTHORITY_FAMILY,
                                                                                               case_id=CASE, domain=ra.AUTHORITY_DOMAIN))
    assert transaction.refuse(["x"]) is False                                              # only a VALIDATED transaction can be refused this way
    transaction.state = ra.VALIDATED
    assert transaction.refuse(["interval_minutes_validated"], reason="r") is True
    assert transaction.state == ra.ABORTED and transaction.committed == () and transaction.rollback["validation_failures"] == ["interval_minutes_validated"]
    with pytest.raises(ra.AuthorityRefused):
        transaction.commit({"sim_time": 3, "observable": {}})


# -- P3-223A: the certified pressure series, both cases -----------------------------------------------------------------------------------------------------

def _series(*, guard: bool):
    rows = []
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        with pytest.MonkeyPatch.context() as patch:
            if not guard:
                patch.setattr(ra.AuthoritySite, "_boundary_guard", lambda self, minute: "")          # the experiment as it was certified, before P3-245's boundary
            rows.extend(series_harness._play_the_battery_with_authority(patch, case))
    return rows


def _fingerprint(rows):
    return ra.digest_of([{"case": row["case"], "scenario": row["scenario"], "halted": row["halted"], "halt_reason": row["halt_reason"], "committed": row["committed"],
                          "minutes": row["minutes"],
                          "pressures": [[m.get("minute"), m.get("outcome"), m.get("common_pressures"), m.get("failure_reason")] for m in row["artifact"]["minutes"]]}
                         for row in rows])


@pytest.fixture(scope="module")
def pressure_series():
    return _series(guard=True)


@pytest.fixture(scope="module")
def pressure_series_before_the_boundary():
    return _series(guard=False)


def test_r2_the_certified_pressure_series_reproduces_exactly_with_the_boundary_neutralized(pressure_series_before_the_boundary):
    """223A (kept as certified). 34 scenarios, 26 complete, 8 stopped, 66 committed minutes, 78 minute records, and the SAME fingerprint as before the repair, when the P3-245
    collapse-boundary guard is neutralized: the repair of P3-223 and the grant of P3-240 change not one byte of the certified experiment."""
    rows = pressure_series_before_the_boundary
    assert len(rows) == 34 and all(row["site"] for row in rows)
    assert (sum(1 for row in rows if not row["halted"]), sum(1 for row in rows if row["halted"])) == (26, 8)
    assert sum(row["committed"] for row in rows) == 66 and sum(row["minutes"] for row in rows) == 78
    assert _fingerprint(rows) == SERIES_FINGERPRINT


def test_r2_with_the_boundary_in_force_only_the_two_terminal_deterioration_scenarios_change(pressure_series, pressure_series_before_the_boundary):
    """P3-245 (declared change): 24 complete, 10 stopped, 62 committed minutes, 78 minute records and the new fingerprint; the other 32 scenarios are identical to the certified
    ones; each ``terminal_deterioration`` stops with ``COLLAPSE_BOUNDARY_REACHED`` at the interval that holds minute 207, its last commit being minute 180."""
    rows, before = pressure_series, pressure_series_before_the_boundary
    assert (sum(1 for row in rows if not row["halted"]), sum(1 for row in rows if row["halted"])) == (24, 10)
    assert sum(row["committed"] for row in rows) == 62 and sum(row["minutes"] for row in rows) == 78
    assert _fingerprint(rows) == SERIES_FINGERPRINT_WITH_THE_BOUNDARY
    changed = [(row["case"], row["scenario"]) for row, old in zip(rows, before) if _fingerprint([row]) != _fingerprint([old])]
    assert changed == [("gi_bleed_57m", "terminal_deterioration"), ("gi_bleed_72f", "terminal_deterioration")], changed
    for row in rows:
        if row["scenario"] == "terminal_deterioration":
            assert row["halted"] and row["halt_reason"].startswith(ra.COLLAPSE_BOUNDARY_REACHED) and row["committed"] == 6 and max(row["artifact"]["authority_minutes"]) == 180
            assert "minute 207" in row["halt_reason"]


def test_r2_the_certified_pressure_series_replays_after_the_repair(pressure_series):
    """223A, the verification half: every digest verifies and the replay covers every committed minute of every COMPLETED scenario."""
    rows = pressure_series
    assert len(rows) == 34 and all(row["site"] for row in rows)
    assert not [m for row in rows for m in row["artifact"]["minutes"] if m.get("interval_validation")], "no certified scenario crossed a failed intermediate minute"
    # the certified criteria of the series: every digest verifies, and the replay covers every committed minute of every COMPLETED scenario (a scenario halted after a
    # commit declares a mixed trajectory and is not asked to reproduce a continuation it never made)
    assert all(row["digest_verified"] for row in rows)
    assert all(row["replay"]["covers_every_committed_minute"] for row in rows if not row["halted"])
