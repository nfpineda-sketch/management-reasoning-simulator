"""P3-217: the REAL page, with the authority OFF and the dormant pair evaluation ON.

TEST-SIDE. The app is driven through Streamlit's own ``AppTest`` exactly as a resident drives it: the three clinical-time routes (a question, an examination, a
wait), an IV line, ordinary orders, a multi-minute infusion, an unsupported action. Nothing is injected and nothing is enabled: no authority flag, no approved
snapshot, no store. Two things are proved here, and they are different claims:

* **Invisibility (P3-217A).** The resident-visible page and the encounter's own state are IDENTICAL with every flag off and with the shadow and the dry
  evaluation on, turn by turn, for both GI cases. The dry evaluation is a reader: it changes nothing the resident sees, nothing the engine holds, nothing the
  record or the score is built from.
* **Reach.** With the dry flag on, the SAME hook the page calls evaluates every turn that moves the clock, on both routes, at the granularity of the actual
  evolution (the 60-minute infusion is validated at its sixty minutes), and says WOULD_COMMIT / NO_ADVANCE / WOULD_ABORT / EXPERIMENT_HALTED. Whatever it says is
  a record of what a transaction WOULD do; it is not a clinical reading and it grants nothing.
"""
import re
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_shadow as rs

APP = str(Path(__file__).resolve().parent / "app.py")
CHALLENGE = "R2-05"
CASES = ("gi_bleed_57m", "gi_bleed_72f")
FOUR_FIELDS = ("What do you think is going on?", "What are you going to do?",
               "What do you expect to happen, or what are you trying to clarify?", "What will you check, and when?")
ANSWERS = ("Haemorrhagic shock from an upper gastrointestinal bleed.", None, "A higher perfusion pressure while the source is controlled.",
           "Blood pressure, heart rate and capillary refill in 15 minutes.")
UNSUPPORTED = "Start norepinephrine at 10 mcg/min."
#: What a resident must never see and the dry evaluation must never leave on the page.
FORBIDDEN_ON_THE_PAGE = ("WOULD_COMMIT", "WOULD_ABORT", "EXPERIMENT_HALTED", "NO_ADVANCE_TURN", "development_authority_view", "phase3_", "GI_DEVELOPMENT_SNAPSHOT",
                         "consciousness_category", "VALIDATED_ATOMIC_INTERVAL", "dry run", "dry-run")


def _clean(monkeypatch, case, *, shadow, dry, authority=None):
    """The page on ``case`` with the flags this test names and, unless ``authority`` is a store directory, no authority flag, no approved snapshot, no store."""
    for name in (ra.AUTHORITY_FLAG, ra.SNAPSHOT_FLAG, ra.ENVIRONMENT_FLAG, store.STORE_FLAG, pair.DRY_FLAG, rs.FLAG, "OPENAI_API_KEY") + tuple(ra.PILOT_FLAGS) + tuple(ra.PILOT_REQUIRED_ON):
        monkeypatch.delenv(name, raising=False)
    for name, value in (("MRS_OFFLINE_CASES", "1"), ("MRS_DEFAULT_CHALLENGE", CHALLENGE), ("MRS_DEFAULT_VARIANT", case)):
        monkeypatch.setenv(name, value)
    if shadow:
        monkeypatch.setenv(rs.FLAG, rs.MODE_SHADOW_COMPARE)
    if dry:
        monkeypatch.setenv(pair.DRY_FLAG, pair.DRY_ON)
    if authority is not None:
        # the ONE existing authorized DEVELOPMENT configuration of the pressure experiment (P3-40): used only by the test that proves the clinical-time route
        for name, value in ((ra.AUTHORITY_FLAG, ra.MODE_LIMITED_COMMON_AUTHORITY), (ra.SNAPSHOT_FLAG, "gi_pressure_committed"), (ra.ENVIRONMENT_FLAG, "development"),
                            (store.STORE_FLAG, str(authority)), (rs.FLAG, rs.MODE_SHADOW_COMPARE)):
            monkeypatch.setenv(name, value)


def _open(monkeypatch, case, *, shadow, dry, authority=None):
    _clean(monkeypatch, case, shadow=shadow, dry=dry, authority=authority)
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=600)
    at.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    at.session_state["_shared_access_granted"] = True
    at.run()
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    assert begin, "the app must offer the encounter"
    begin[0].click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert str(at.session_state["state"].get("engine_family") or "") == "gi_bleed" and at.session_state["state"].get("case_id")
    return at


def _screen(at):
    """Everything a resident can read: markdown, captions, plain text, headings, info/warning/error boxes, metrics, the form and button labels."""
    parts = []
    for kind in ("markdown", "caption", "text", "title", "header", "subheader", "info", "warning", "error", "success"):
        parts.extend(str(item.value) for item in getattr(at, kind, []))
    parts.extend(f"{item.label}={item.value}" for item in getattr(at, "metric", []))
    parts.extend(str(item.label) for item in at.button)
    return "\n".join(parts)


def _mode(at, name):
    next(r for r in at.radio if r.label == "Encounter").set_value(name).run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _answer_the_gate(at):
    for label, answer in zip(FOUR_FIELDS, ANSWERS):
        if answer is not None:
            next(item for item in at.text_area if item.label == label).set_value(answer)
    next(b for b in at.button if b.label == "Complete reasoning & execute held order").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    # P3-271 (declared adaptation): the held order is consumed by the turn that runs it. When a real authority session REFUSES that turn the encounter is untouched by it, so the hold is still there: it may
    # remain only if the authority site halted (any other leftover hold is still a failure).
    site = at.session_state.get(ra.SITE_KEY)
    assert not at.session_state["pending_reasoning"] or (site is not None and site.halted), "the held order must have been consumed by the turn that ran it"


def _order(at, text):
    """One order as a resident gives it: the Treat mode, the text, Send; and the four answers when the page's gate holds the order."""
    _mode(at, "Treat")
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Send").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    if at.session_state["pending_reasoning"]:
        _answer_the_gate(at)


def _ask(at, question="What brought you in today?"):
    _mode(at, "Talk")
    next(item for item in at.text_input if "Ask" in str(item.label)).set_value(question)
    next(b for b in at.button if b.label == "Ask").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _examine(at):
    _mode(at, "Examine")
    next(b for b in at.button if b.label == "Examine patient").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


#: The only things that differ between two runs of the same script WITHOUT any flag: the random case id of the encounter, the random per-submission id the
#: order ids start with, and the wall-clock stamp of a submission. They are masked; nothing else is.
_PER_RUN = {"case_id", "order_id", "submission_id", "received_at"}


def _masked(value, parent=None):
    if isinstance(value, dict):
        return {key: ("<per-run>" if key in _PER_RUN or (key == "id" and parent == "submission") else _masked(item, key)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_masked(item, parent) for item in value]
    return value


def _minute(at):
    return int(at.session_state["state"].get("sim_time", 0) or 0)


#: The resident's script. Each step is (label, driver). The unsupported action is LAST: it is what ends a dry experiment.
SCRIPT = (("question", _ask), ("examination", _examine), ("iv_line", lambda at: _order(at, "Place an IV line.")),
          ("wait", lambda at: _order(at, "Reassess in 10 minutes.")), ("bolus", lambda at: _order(at, "Give 500 mL normal saline over 5 minutes.")),
          ("infusion", lambda at: _order(at, "Give 1000 mL normal saline over 60 minutes.")), ("unsupported", lambda at: _order(at, UNSUPPORTED)),
          ("wait_after", lambda at: _order(at, "Reassess in 15 minutes.")))


def _play(monkeypatch, case, *, shadow, dry):
    """The script on one page. Returns the screen and the engine's own state after EVERY step."""
    at = _open(monkeypatch, case, shadow=shadow, dry=dry)
    trail = [("arrival", _screen(at), _observed(at))]
    for label, drive in SCRIPT:
        drive(at)
        trail.append((label, _screen(at), _observed(at)))
    return at, trail


def _observed(at):
    state = at.session_state["state"]
    return {"sim_time": int(state.get("sim_time", 0) or 0), "observable": deepcopy(dict(state.get("observable") or {})),
            "events": [(item.get("kind"), item.get("text")) for item in at.session_state["events"]],
            # an order's id starts with a per-submission random prefix: what is compared is its position in the turn and its settled fate
            "ledger": [(str(row.get("order_id")).split(":")[-1], row.get("fate")) for row in at.session_state.get("order_ledger", [])]}


@pytest.fixture(scope="module", params=CASES)
def pages(request):
    """Both pages for one case, played with the SAME script: everything off (the default) and the shadow plus the dry evaluation on."""
    mp = pytest.MonkeyPatch()
    try:
        case = request.param
        off, trail_off = _play(mp, case, shadow=False, dry=False)
        on, trail_on = _play(mp, case, shadow=True, dry=True)
        yield {"case": case, "off": off, "on": on, "trail_off": trail_off, "trail_on": trail_on}
    finally:
        mp.undo()


def test_p1_the_resident_page_and_the_engine_state_are_identical_turn_by_turn_with_the_dry_evaluation_on(pages):
    """P3-217A. Both routes, both cases: the visible text, the observable the engine holds, the event stream and the order ledger do not differ by one character."""
    assert [row[0] for row in pages["trail_on"]] == [row[0] for row in pages["trail_off"]]
    for (label, screen_off, seen_off), (_, screen_on, seen_on) in zip(pages["trail_off"], pages["trail_on"]):
        assert screen_on == screen_off, f"{pages['case']}/{label}: the resident-visible page differs with the dry evaluation on"
        assert seen_on == seen_off, f"{pages['case']}/{label}: the engine's own state differs with the dry evaluation on"
    assert _minute(pages["on"]) == _minute(pages["off"]) > 60


def test_p2_nothing_of_the_dry_evaluation_is_ever_on_the_page_or_in_what_the_record_is_built_from(pages):
    for label, screen, _ in pages["trail_on"]:
        for word in FORBIDDEN_ON_THE_PAGE:
            assert word not in screen, (pages["case"], label, word)
    at = pages["on"]
    state = at.session_state["state"]
    assert "development_authority_view" not in state, "the overlay lives only in a prepared COPY, and the dry run never writes one"
    assert state["observable"].get("mental_status") == pages["off"].session_state["state"]["observable"].get("mental_status")
    for key in (ra.SITE_KEY, ra.ARTIFACT_KEY, ra.HALTED_KEY):
        assert at.session_state.get(key) is None, key
    # the management trace and the learner-visible snapshots are built from the legacy state, which the dry run never touched
    assert [item.get("kind") for item in at.session_state["management_trace"]] == [item.get("kind") for item in pages["off"].session_state["management_trace"]]
    assert _masked(at.session_state["management_trace"]) == _masked(pages["off"].session_state["management_trace"]), "the trace is identical but for per-run identifiers"


def test_p3_with_the_flags_off_the_page_holds_no_pair_state_at_all(pages):
    off = pages["off"]
    for key in (pair.DRY_KEY, pair.DRY_ARTIFACT_KEY, pair.DRY_REFUSAL_KEY, "phase3_shadow", ra.SITE_KEY, ra.ARTIFACT_KEY):
        assert off.session_state.get(key) is None, key


def test_p4_the_dry_evaluation_saw_every_route_the_clock_moved_by_and_validated_the_infusion_minute_by_minute(pages):
    held = pages["on"].session_state[pair.DRY_KEY]
    evaluator = held[1]
    assert evaluator is not None and held[0] is pages["on"].session_state["phase3_shadow"] and pages["on"].session_state[pair.DRY_REFUSAL_KEY] is None
    records = evaluator.records
    routes = {row["route"] for row in records}
    assert routes == {ra.ORDER_TURN, ra.CLINICAL_TIME}, routes                         # the question and the examination are not invisible to it
    first = records[0]
    assert first["route"] == ra.CLINICAL_TIME and first["minute"] == 2 and first["verdict"] == pair.WOULD_COMMIT, (first["minute"], first["failed_checks"])
    longest = max(records, key=lambda row: len(row["interval"]))
    assert len(longest["interval"]) >= 60 and all(row["ok"] for row in longest["interval"]) and longest["verdict"] == pair.WOULD_COMMIT, "the infusion is validated at every minute"
    assert [row["minute"] for row in longest["interval"]] == list(range(longest["minute"] - len(longest["interval"]) + 1, longest["minute"] + 1))
    assert not evaluator.violations, evaluator.violations


def test_p5_the_iv_line_is_acknowledged_as_executed_without_physiology_and_does_not_stop_the_experiment(pages):
    evaluator = pages["on"].session_state[pair.DRY_KEY][1]
    iv = [row for row in evaluator.records if row["no_common_physiology"]]
    assert iv, "the IV line turn left a record"
    assert iv[0]["verdict"] == pair.NO_ADVANCE and iv[0]["no_common_physiology"][0]["disposition"] == ra.EXECUTED_NO_COMMON_PHYSIOLOGY, iv[0]
    assert iv[0]["no_common_physiology"][0]["contributor"] is None and iv[0]["no_common_physiology"][0]["physiological_mutation"] is False
    later = [row for row in evaluator.records if row["minute"] > iv[0]["minute"] and row["verdict"] == pair.WOULD_COMMIT]
    assert later, "the experiment went on after the IV line"


def test_p6_the_unsupported_action_ends_the_experiment_visibly_and_nothing_continues_after_it(pages):
    evaluator = pages["on"].session_state[pair.DRY_KEY][1]
    summary = evaluator.summary()
    assert evaluator.halt is not None and "supported_management" in evaluator.halt["failed_checks"], evaluator.halt
    assert summary["authority_had_begun_at_abort"] is True and "INVALID_FOR_CONTINUATION" in summary["consequence"]
    abort = next(row for row in evaluator.records if row["verdict"] == pair.WOULD_ABORT)
    assert abort["would_write"] is None
    after = [row for row in evaluator.records if row["minute"] > abort["minute"] or row is not abort and evaluator.records.index(row) > evaluator.records.index(abort)]
    assert after and all(row["verdict"] == pair.HALTED for row in after), [row["verdict"] for row in after]
    assert summary["would_commit_minutes"] == len(evaluator.would_commit) and max(evaluator.would_commit) < abort["minute"] + 1


def test_p7_the_page_stored_the_evaluator_beside_the_shadow_session_and_summarised_it_without_a_clinical_claim(pages):
    artifact = pages["on"].session_state[pair.DRY_ARTIFACT_KEY]
    assert artifact["snapshot_is_the_pinned_version_1"] is True and artifact["granularity"] == pair.VALIDATED_ATOMIC_INTERVAL
    assert artifact["snapshot"]["snapshot_id"] == "GI_DEVELOPMENT_SNAPSHOT_V1" and artifact["case"] == pages["case"]
    assert artifact["routes"] == [ra.CLINICAL_TIME, ra.ORDER_TURN] and artifact["violations"] == []
    assert re.fullmatch(r"[0-9a-f]{64}", artifact["record_digest"])


# -- the collapse-boundary approach: waiting, untreated, until the experimental window or the boundary ends the dry experiment ---------------------------------

@pytest.mark.parametrize("case", CASES)
def test_p8_an_untreated_wait_approaches_the_window_and_the_boundary_without_the_page_changing(monkeypatch, case):
    waits = ("Reassess in 60 minutes.",) * 5
    texts = {}
    for label, dry in (("off", False), ("on", True)):
        at = _open(monkeypatch, case, shadow=dry, dry=dry)
        trail = []
        for text in waits:
            _order(at, text)
            trail.append((_screen(at), _observed(at)))
        texts[label] = (at, trail)
    assert [row[0] for row in texts["on"][1]] == [row[0] for row in texts["off"][1]]
    assert [row[1] for row in texts["on"][1]] == [row[1] for row in texts["off"][1]]
    evaluator = texts["on"][0].session_state[pair.DRY_KEY][1]
    assert evaluator is not None and evaluator.records
    # the window or the boundary stops the experiment; whichever does, it is named, it commits nothing after it, and the encounter simply went on
    assert evaluator.halt is not None, "five hours of waiting must reach the 240-minute window or the collapse boundary"
    assert set(evaluator.halt["failed_checks"]) & {"window_open", "collapse_boundary_not_reached"}, evaluator.halt
    assert _minute(texts["on"][0]) == _minute(texts["off"][0]) == 300
    assert all(row["verdict"] == pair.HALTED for row in evaluator.records[evaluator.records.index(next(r for r in evaluator.records if r["verdict"] == pair.WOULD_ABORT)) + 1:])


# -- P3-215 on the real page, with the existing authorized DEVELOPMENT experiment of the pressure (not the default; the test sets the flags) ---------------------

def test_p9_with_the_development_pressure_experiment_a_first_question_opens_the_site_before_the_time_passes_and_commits_its_minute(monkeypatch, tmp_path):
    """The clinical-time route used to reach the shadow and never the authority site (C9). With the hook, the first thing a resident does -- ask a question,
    two minutes of clinical time -- opens the site while the state is still the arrival, and commits that minute on the clinical-time route; the next order
    turn commits its own on the order-turn route. Both write only the pressure domain."""
    at = _open(monkeypatch, "gi_bleed_57m", shadow=True, dry=False, authority=tmp_path / "authority_store")
    assert at.session_state.get(ra.SITE_KEY) is None
    _ask(at)
    site = at.session_state.get(ra.SITE_KEY)
    assert site is not None and not site.halted, "a first question must not leave the encounter without the experiment its configuration asked for"
    assert site.minutes_committed == (2,), site.minutes_committed
    first = site.artifact()["minutes"][0]
    assert first["route"] == ra.CLINICAL_TIME and first["provenance_settled"] is True and first["outcome"] == ra.COMMITTED
    assert set(first["moved_fields"]) <= {"sbp", "dbp", "map"}
    _order(at, "Reassess in 5 minutes.")
    assert site.minutes_committed == (2, 7) and not site.halted
    assert site.artifact()["minutes"][1].get("route") != ra.CLINICAL_TIME
    assert at.session_state.get(pair.DRY_KEY) is None, "a real site open: the dry evaluation is not fed a minute the real transaction already wrote"
