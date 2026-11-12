"""P3-219: the findings of the independent review of this cycle (each CONFIRMED with the reviewer's own probe before it was corrected), and the mutants and
negative controls of the twelve attacks the assignment names.

TEST-SIDE. Nothing here enables an authority: sites open through the test-only approval of the P3-28 certification and every commit is made on a copy.

Findings (severity from the review):
  F1 HIGH    a turn that did not advance the clock was never settled against the ledger: "Place an IV line. Also give <something the mapping cannot
             represent>" kept the experiment going (the unmodelled order appears ONLY in the settled ledger).
  F2 MEDIUM  a capture that failed (``before=None``) let a multi-minute turn commit a pressure that ignored the turn's treatment; kind-less gaps were dropped.
  F3 MEDIUM  a failure stamped at the turn's start, or recorded during a no-advance turn, was never judged.
  F4 MEDIUM  ``trace_phase0.observation_snapshot`` read the live word with a dynamic key and persisted it into every trace event, unrouted.
  F5 LOW     a refused pair could be re-validated and committed.
  F6 LOW     a malformed overlay made the view raise; a float category was accepted as a rung.
  F7 LOW     the dry settlement compared the raw class, not the normalised one.
  F8 LOW     the evaluator did not compare its case with the session's; a stale artifact survived into the next encounter; the dry replay was quadratic.

Mutants: each ``test_m*`` removes ONE defense and shows that the attack it stops then gets through, while the real code stops it.
"""
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
CASE = "gi_bleed_57m"
TEST_ONLY_SNAPSHOT = {"id": "test_only_findings_point", "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID, "parameters": {"test_only_placeholder": 1.0}}
STORE_DIR = tempfile.mkdtemp(prefix="phase3-findings-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"], ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE, store.STORE_FLAG: STORE_DIR}


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


def _encounter():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        return acceptance.Encounter(CASE)


def _turn(encounter, text):
    before = encounter.shadow.capture(encounter.state)
    entry = encounter.order(text)
    return before, entry, [dict(item) for item in entry["orders"]]


def _site(arrival, approved):
    site = ra.open_site(arrival, environ=approved)
    assert site is not None
    return site


def _iv_turn(text):
    """A turn at the arrival whose first order is the IV line. Returns what the site and the evaluator are handed."""
    real, seen = acceptance.Encounter._execute, {}

    def execute(self, parsed, line):
        out = real(self, parsed, line)
        seen["run"] = out[2]
        return out
    acceptance.Encounter._execute = execute
    try:
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter(CASE)
            arrival = deepcopy(encounter.state)
            before = encounter.shadow.capture(encounter.state)
            entry = encounter.order(text)
    finally:
        acceptance.Encounter._execute = real
    return {"arrival": arrival, "before": before, "after": deepcopy(encounter.state), "session": encounter.shadow, "ran": seen["run"], "entry": entry,
            "orders": [dict(item) for item in entry["orders"]], "sid": str(entry["orders"][0].get("submission_id") or "")}


# -- F1 ---------------------------------------------------------------------------------------------------------------------------------------------------

def test_f1_an_unmodelled_order_beside_an_iv_line_halts_the_real_site_at_settlement_and_a_plain_iv_line_does_not(approved):
    plain = _iv_turn("Place an IV line.")
    site = _site(plain["arrival"], approved)
    assert site.minute(plain["before"], deepcopy(plain["after"]), plain["session"], plain["ran"], plain["sid"], ra.ORDER_TURN) is None and not site.halted
    report = site.settle_provenance(plain["sid"], plain["orders"])
    assert not site.halted and not report["halted"] and site.no_advance_turns[-1]["provenance_settled"] is True, report
    mixed = _iv_turn("Place an IV line. Also give ondansetron 4 mg IV.")
    assert {row.get("class") for row in mixed["orders"]} >= {"vascular_access", "not_modelled"}
    site = _site(mixed["arrival"], approved)
    assert site.minute(mixed["before"], deepcopy(mixed["after"]), mixed["session"], mixed["ran"], mixed["sid"], ra.ORDER_TURN) is None and not site.halted   # as before: the ledger is the only trace
    report = site.settle_provenance(mixed["sid"], mixed["orders"])
    assert site.halted and report["halted"] and ra.PROVENANCE_CONTRADICTION in site.halt_reason and "not_modelled" in str(report["unsupported"]), report
    # the dry evaluator reaches the same conclusion by the SAME rule
    dry = pair.PairDryEvaluator(pair.bind(), CASE, mixed["arrival"])
    dry.minute(mixed["before"], deepcopy(mixed["after"]), mixed["session"], mixed["ran"], mixed["sid"], ra.ORDER_TURN)
    dry.settle(mixed["orders"])
    assert dry.halt is not None and dry.halt["failed_checks"] == ["settled_classes_supported"]


def test_f7_the_shared_settlement_rule_normalises_the_class_and_judges_the_fate():
    rows = [{"class": "Vascular_Access", "fate": "HELD_CLARIFICATION"}, {"class": " VASCULAR_ACCESS ", "fate": "RECORDED_NOT_MODELLED"}, {"class": "fluid", "fate": "EXECUTED"}]
    assert ra.unsupported_in_settlement(rows) == ("vascular_access",)
    assert ra.unsupported_in_settlement([{"class": "VASCULAR_ACCESS", "fate": "EXECUTED"}, {"class": "vascular_access", "fate": "DUPLICATE_IGNORED"}]) == ()
    assert ra.unsupported_in_settlement([{"class": "intubation", "fate": "EXECUTED"}, {}, {"class": None}]) == ("intubation", "untyped_action")
    assert ra.unsupported_in_settlement(None) == ()


# -- F2 / F3 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_f2_a_capture_that_failed_cannot_let_a_multi_minute_turn_commit_a_pressure_that_ignores_its_treatment(approved, monkeypatch):
    real_capture = rs.ShadowSession.capture

    def capture(self, state):
        self.failures.append(rs._failure(int(state.get("sim_time", 0) or 0), "capture", RuntimeError("could not copy"), rs.MAPPING_GAP))
        return None
    real, seen = acceptance.Encounter._execute, {}

    def execute(self, parsed, line):
        out = real(self, parsed, line)
        seen["run"] = out[2]
        return out
    monkeypatch.setattr(acceptance.Encounter, "_execute", execute)
    monkeypatch.setattr(rs.ShadowSession, "capture", capture)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(real_capture(encounter.shadow, encounter.state))
        before = encounter.shadow.capture(encounter.state)
        assert before is None
        encounter.order("Give 500 mL normal saline over 10 minutes.")
    assert encounter.shadow.gaps and not [gap for gap in encounter.shadow.gaps if gap.get("kind")], "the gap of a lost capture names no kind"
    site = _site(arrival, approved)
    out = site.minute(None, deepcopy(encounter.state), encounter.shadow, seen["run"], "fl-1", ra.ORDER_TURN)
    assert out is None and site.halted and site.minutes_committed == (), "the site must not commit a pressure that never saw the bolus"
    # and the shared reading of a gap with no kind is unsupported, in the site and in the evaluator
    assert ra.gap_kinds_of(encounter.shadow) == (ra.UNTYPED_GAP,) * len(encounter.shadow.gaps) and ra.unsupported_among(ra.gap_kinds_of(encounter.shadow))


def test_f3_a_failure_stamped_at_the_turn_start_refuses_the_turn_on_the_real_site(approved):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before = encounter.shadow.capture(encounter.state)
        entry = encounter.order("Give 500 mL normal saline over 8 minutes.")
    encounter.shadow.failures.append(rs.ShadowFailure(0, "observe", "RuntimeError", "recorded at the turn's first minute", rs.UNEXPECTED))
    site = _site(arrival, approved)
    ran = [dict(item) for item in entry["orders"]]
    assert site.minute(before, deepcopy(encounter.state), encounter.shadow, ran, "t1", ra.ORDER_TURN) is None and site.halted and site.minutes_committed == ()


def test_f3_a_failure_recorded_during_a_turn_that_did_not_move_the_clock_is_judged_by_the_site_and_by_the_evaluator(approved):
    quiet = _iv_turn("Place an IV line.")
    quiet["session"].failures.append(rs.ShadowFailure(0, "observe", "RuntimeError", "injected during the IV turn", rs.UNEXPECTED))
    site = _site(quiet["arrival"], approved)
    assert site.minute(quiet["before"], deepcopy(quiet["after"]), quiet["session"], quiet["ran"], quiet["sid"], ra.ORDER_TURN) is None
    assert site.halted and site.no_advance_turns == [], "the turn is not recorded as 'nothing happened'"
    dry = pair.PairDryEvaluator(pair.bind(), CASE, quiet["arrival"])
    record = dry.minute(quiet["before"], deepcopy(quiet["after"]), quiet["session"], quiet["ran"], quiet["sid"], ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_ABORT and "common_run_did_not_fail" in record["failed_checks"], record["failed_checks"]


def test_f3_a_failure_that_an_earlier_turn_judged_is_not_judged_again_and_a_clean_run_is_never_refused(approved):
    """Negative control: the high-water mark advances with every judged turn, so only NEW failures refuse."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before = encounter.shadow.capture(encounter.state)
        advance_clinical_time(encounter.state, 3, label="history_question")
        encounter.shadow.observe_time(before, encounter.state, {})
    site = _site(arrival, approved)
    assert site.minute(before, deepcopy(encounter.state), encounter.shadow, None, "q1", ra.CLINICAL_TIME) is not None and site.failures_judged == len(encounter.shadow.failures) == 0
    before2 = encounter.shadow.capture(encounter.state)
    advance_clinical_time(encounter.state, 2, label="history_question")
    encounter.shadow.observe_time(before2, encounter.state, {})
    assert site.minute(before2, deepcopy(encounter.state), encounter.shadow, None, "q2", ra.CLINICAL_TIME) is not None and not site.halted


# -- F4 ---------------------------------------------------------------------------------------------------------------------------------------------------

def test_f4_the_trace_snapshot_of_what_the_resident_saw_is_routed_and_never_carries_the_common_word():
    import trace_phase0
    state = {"sim_time": 7, "observable": {"sbp": 88, "dbp": 54, "mental_status": "Alert", "pulse_present": True}}
    state[view.OVERLAY_KEY] = {"owner": "t", "minute": 7, "views": {}, "common": {"consciousness_category": 3, "mental_status": view.WORDS[3], "pulse_present": True},
                               "legacy": {"mental_status": "Alert"}, "mapped_into_live_field": True}
    state["observable"]["mental_status"] = view.WORDS[3]                    # the mapped mutant: the common word forced into the live field
    assert trace_phase0.observation_snapshot(state)["visible"]["mental_status"] == "Alert", "the view preserves the legacy word for this reader"
    assert "trace_phase0.py::observation_snapshot" in view.ROUTED_READERS
    plain = {"sim_time": 1, "observable": {"sbp": 88, "mental_status": "Drowsy", "crt": 5}}
    assert trace_phase0.observation_snapshot(plain)["visible"] == {"sbp": 88, "mental_status": "Drowsy", "crt": 5}
    assert list(trace_phase0.observation_snapshot({"sim_time": 1, "observable": {"crt": 5, "sbp": 1, "mental_status": "x", "hr": 2}})["visible"]) == ["sbp", "hr", "mental_status", "crt"]


# -- F5 / F6 / F8 ---------------------------------------------------------------------------------------------------------------------------------------

def _pair_tx(bound, state):
    tx = pair.PairAuthorityTransaction(minute=int(state["sim_time"]), case_id=CASE, snapshot=TEST_ONLY_SNAPSHOT, bound=bound)
    payload = pair.PairPayload(minute=int(state["sim_time"]), sbp=88, dbp=54, map=ra.derived_map(88, 54), consciousness_category=3, mental_status=pair.WORD_OF[3], pulse_present=True)
    tx.capture(state).compute(payload, {"sbp": 90, "dbp": 55})
    return tx


def test_f5_a_refused_pair_cannot_be_revalidated_with_better_arguments_and_committed(bound, approved):
    state = deepcopy(_encounter().state)
    good = ra.digest_of({"sbp": 88.4, "dbp": 54.1, "map": 65.5})
    pressure = dict(invariants_hold=True, replay_digest=good, expected_digest=good, unsupported=(), legacy_arrest=False, failures=())
    tx = _pair_tx(bound, state)
    assert tx.validate(pressure=pressure, consciousness_ok={}, interval_ok=False, boundary_clear=True, window_open=True, one_course=True) is False and tx.state == pair.PAIR_ABORTED
    with pytest.raises(ra.AuthorityRefused):
        tx.validate(pressure=pressure, consciousness_ok={}, interval_ok=True, boundary_clear=True, window_open=True, one_course=True)
    with pytest.raises(ra.AuthorityRefused):
        tx.commit(state, environ=approved)
    assert tx.state == pair.PAIR_ABORTED and tx.committed == ()


def test_f6_a_malformed_overlay_never_raises_into_a_reader_and_a_float_category_is_not_a_rung():
    state = {"sim_time": 3, "observable": {"mental_status": "Alert"}}
    for category in (3.0, True, "3", None, [3], float("nan")):
        state[view.OVERLAY_KEY] = {"owner": "t", "minute": 3, "views": {}, "common": {"consciousness_category": category, "mental_status": view.WORDS[3], "pulse_present": True},
                                   "legacy": {}, "mapped_into_live_field": False}
        assert view.structure_problems(state[view.OVERLAY_KEY]) == ["common_word_is_not_the_category"], category
        assert view.mental_status_for(state, "family_engine.py::_order", "default") == "Alert"
    state[view.OVERLAY_KEY] = object()
    assert view.mental_status_for(state, "family_engine.py::_order") == "Alert"
    payload = pair.PairPayload(minute=3, sbp=88, dbp=54, map=ra.derived_map(88, 54), consciousness_category=3.0, mental_status=pair.WORD_OF[3], pulse_present=True)
    assert "category_not_on_the_ladder" in pair.payload_problems(payload)


def test_f8_an_evaluator_labelled_with_another_case_is_refused_and_a_stale_artifact_does_not_survive_into_the_next_encounter(bound):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before = encounter.shadow.capture(encounter.state)
        advance_clinical_time(encounter.state, 3, label="history_question")
        encounter.shadow.observe_time(before, encounter.state, {})
    wrong = pair.PairDryEvaluator(bound, "gi_bleed_72f", arrival)
    record = wrong.minute(before, deepcopy(encounter.state), encounter.shadow, None, "q", ra.CLINICAL_TIME)
    assert record["verdict"] == pair.WOULD_ABORT and "case_eligible" in record["failed_checks"], record["failed_checks"]
    held = {pair.DRY_ARTIFACT_KEY: {"case": "gi_bleed_57m", "of": "the previous patient"}}
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        opioid = acceptance.Encounter("opioid_35m")
    assert pair.dry_evaluator_for(held, opioid.shadow, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE, pair.DRY_FLAG: pair.DRY_ON}) is None
    assert pair.DRY_ARTIFACT_KEY not in held


def test_f8_the_dry_replay_is_computed_once_per_turn_and_not_once_per_minute(bound, monkeypatch):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before, entry, ran = _turn(encounter, "Give 500 mL normal saline over 30 minutes.")
    calls = []
    real = pair.fam.replay_shadow_encounter
    monkeypatch.setattr(pair.fam, "replay_shadow_encounter", lambda *a, **k: calls.append(1) or real(*a, **k))
    dry = pair.PairDryEvaluator(bound, CASE, arrival)
    record = dry.minute(before, deepcopy(encounter.state), encounter.shadow, ran, "inf", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_COMMIT and len(record["interval"]) == 30 and len(calls) == 1, (record["failed_checks"], len(calls))


# -- the twelve attacks of P3-219: mutants and negative controls -------------------------------------------------------------------------------------

def test_m1_without_the_interval_check_a_hidden_intermediate_failure_commits_and_with_it_it_does_not(bound, monkeypatch):
    def attack():
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter(CASE)
            arrival = deepcopy(encounter.state)
            before, entry, ran = _turn(encounter, "Give 500 mL normal saline over 30 minutes.")
        results = encounter.shadow.runner.results
        index = next(position for position, item in enumerate(results) if int(item.minute) == 12)
        results[index] = dataclasses.replace(results[index], derived={**dict(results[index].derived), "sbp": None})
        return pair.PairDryEvaluator(bound, CASE, arrival).minute(before, deepcopy(encounter.state), encounter.shadow, ran, "inf", ra.ORDER_TURN)
    assert attack()["verdict"] == pair.WOULD_ABORT
    # DEFENSE IN DEPTH: a hidden intermediate minute is stopped by TWO independent checks -- the per-minute interval validation and the per-minute comparison of
    # the pressure run with the bound run. Remove one and the attack is still stopped; remove both and the end minute alone is judged, and it commits.
    # P3-222 (declared adaptation): the interval check moved behind ``validate_interval`` (the shared primitive's seam); the mutant removes it THERE. What the test
    # protects is unchanged: the two independent per-minute checks, and what happens when both are gone.
    monkeypatch.setattr(pair.PairDryEvaluator, "validate_interval", lambda self, *a, **k: {"mode": None, "rows": [], "ok": True, "first_failed_minute": None, "failed": None,
                                                                                         "ineligible_after": [], "interval_minutes": []})
    assert attack()["verdict"] == pair.WOULD_ABORT, "the one-course comparison still covers every minute of the turn"
    monkeypatch.setattr(pair, "SHARED_READINGS", ())
    assert attack()["verdict"] == pair.WOULD_COMMIT, "with both gone, only the end minute is judged: this is why the two checks are kept"


def test_m2_a_clock_advance_the_hook_never_saw_is_caught_fail_closed_by_the_next_turn(bound):
    """Attack: the time passes outside the hook (a route nobody wired). The next turn the evaluator sees starts at a minute it never saw: ``turn_was_observed``."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before = encounter.shadow.capture(encounter.state)
        advance_clinical_time(encounter.state, 4, label="history_question")                 # the unwired advance: observed by the shadow, never by the evaluator
        encounter.shadow.observe_time(before, encounter.state, {})
        before2 = encounter.shadow.capture(encounter.state)
        advance_clinical_time(encounter.state, 2, label="history_question")
        encounter.shadow.observe_time(before2, encounter.state, {})
    dry = pair.PairDryEvaluator(bound, CASE, arrival)
    record = dry.minute(before2, deepcopy(encounter.state), encounter.shadow, None, "q2", ra.CLINICAL_TIME)
    assert record["verdict"] == pair.WOULD_ABORT and "turn_was_observed" in record["failed_checks"], record["failed_checks"]


def test_m3_without_the_no_advance_rule_the_iv_line_first_turn_would_halt_and_with_it_it_does_not(approved, monkeypatch):
    turn = _iv_turn("Place an IV line.")
    site = _site(turn["arrival"], approved)
    assert site.minute(turn["before"], deepcopy(turn["after"]), turn["session"], turn["ran"], turn["sid"], ra.ORDER_TURN) is None and not site.halted
    monkeypatch.setattr(ra.AuthoritySite, "_no_advance", staticmethod(lambda before, after: False))
    broken = _site(turn["arrival"], approved)
    broken.minute(turn["before"], deepcopy(turn["after"]), turn["session"], turn["ran"], turn["sid"], ra.ORDER_TURN)
    assert broken.halted, "the IV line wrongly halts when the rule is gone (FD-P3-NEW-03)"


def test_m4_widening_the_allowlist_lets_an_unsupported_class_continue_and_the_real_allowlist_does_not(monkeypatch):
    assert ra.unsupported_among(("intubation",)) == ("intubation",)
    widened = dict(ra.NO_COMMON_PHYSIOLOGY_ACTIONS)
    widened["intubation"] = "mutant"
    monkeypatch.setattr(ra, "NO_COMMON_PHYSIOLOGY_ACTIONS", widened)
    assert ra.unsupported_among(("intubation",)) == (), "the allowlist is the one door: widen it and an unsupported action continues"


def test_m5_the_forged_snapshot_is_refused_by_the_evaluator_and_by_the_binding(bound):
    forged = dataclasses.replace(bound, snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V2")
    with pytest.raises(pair.SnapshotBindingError):
        pair.PairDryEvaluator(forged, CASE, {"sim_time": 0})
    values = dict(bound.values)
    first = sorted(values)[0]
    values[first] = values[first] + 1e-9
    with pytest.raises(pair.SnapshotBindingError):
        pair.PairDryEvaluator(dataclasses.replace(bound, values=tuple(sorted(values.items()))), CASE, {"sim_time": 0})


def test_m6_an_evaluator_that_writes_the_state_is_caught_by_its_own_guard(bound, monkeypatch):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        before = encounter.shadow.capture(encounter.state)
        advance_clinical_time(encounter.state, 3, label="history_question")
        encounter.shadow.observe_time(before, encounter.state, {})
    real = pair.PairDryEvaluator._evaluate

    def writing(self, record, minute, before, after, *args, **kwargs):
        out = real(self, record, minute, before, after, *args, **kwargs)
        return out
    state = encounter.state
    dry = pair.PairDryEvaluator(bound, CASE, arrival)
    seen = deepcopy(state)
    record = dry.minute(before, state, encounter.shadow, None, "q", ra.CLINICAL_TIME)
    assert state == seen and not dry.violations, "the real evaluator leaves the state it was handed untouched"
    monkeypatch.setattr(pair.PairDryEvaluator, "_candidate", lambda self, minute: state.__setitem__("sim_time", state["sim_time"] + 1) or None)
    mutant = pair.PairDryEvaluator(bound, CASE, arrival)
    mutant.minute(before, state, encounter.shadow, None, "q", ra.CLINICAL_TIME)
    assert mutant.violations and "encounter_state_untouched" in mutant.records[-1]["failed_checks"], "a writer is caught by the digest guard"
    assert record["route"] == ra.CLINICAL_TIME


def test_m7_the_hook_with_a_broken_evaluator_never_raises_into_the_turn_and_never_writes(monkeypatch):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        before = encounter.shadow.capture(encounter.state)
        advance_clinical_time(encounter.state, 3, label="history_question")
        encounter.shadow.observe_time(before, encounter.state, {})
    monkeypatch.setattr(pair.PairDryEvaluator, "summary", lambda self: (_ for _ in ()).throw(RuntimeError("summary broke")))
    held = {}
    digest = ra.digest_of(encounter.state)
    assert pair.after_clock_moved(held, encounter.shadow, before, encounter.state, None, None, ra.CLINICAL_TIME, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE, pair.DRY_FLAG: pair.DRY_ON}) is None
    assert held[pair.DRY_REFUSAL_KEY].startswith("HOOK_FAILED") and ra.digest_of(encounter.state) == digest
