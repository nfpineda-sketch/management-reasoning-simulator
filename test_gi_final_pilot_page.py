"""P3-540 to P3-550 (FD-FINALPILOT-01 to 10) on the REAL page (Streamlit AppTest, synthetic accounts, ``app.py``): the final pre-pilot convergence of the GI development pilot.

The resident flows (P3-540, P3-548): an incomplete order is held, the reader asks, nothing is carried out, the live development authority stays on the SAME committed minute (a
proven clarification no-op) and the encounter goes on; the completed order then runs normally. The norepinephrine clarifications (units, restart, a MAP target), consecutive
clarifications and a turn that mixes a complete order with an incomplete one are certified end to end. The boundary (P3-541): every definitive-control phrasing ends the encounter
before anything reaches the engine, and an executed consultation of a definitive service cannot run even if every word-based reading missed it. Mental status (P3-542): once
norepinephrine has been given, Talk mode is withheld and no mental-status word is shown. Robustness (P3-545, P3-550): a rerun keeps the held order, a new session records the
open encounter INTERRUPTED at once, a faculty stop during a clarification ends the encounter before the pending order runs, the replay review matches after no-ops, and an order
the authority does not represent still fails closed.
"""
import json

import pytest

import gi_pilot as gp
import gi_pilot_ui as gpu
import runtime_authority as ra
import test_phase3_pair_page as page
from test_gi_pilot_page import INTERNALS, ORDERS, _account, _begin, _pilot, _screen, _sign_in, _store, world  # noqa: F401  (world is the module-scoped fixture)

pytestmark = pytest.mark.ordinary_configuration
BOX = "Enter your clinical reasoning and/or actions"
MENTAL = ("Alert", "Drowsy", "Obtunded", "Unresponsive", "Confused", "Lethargic", "Agitated", "Sedated", "Comatose")


def _send(at, text):
    """One submission as a resident types it (Treat mode, Send); the reasoning gate is answered when it holds the order."""
    page._mode(at, "Treat")
    next(a for a in at.text_area if a.label == BOX).set_value(text)
    next(b for b in at.button if b.label == "Send").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    if at.session_state["pending_reasoning"]:
        page._answer_the_gate(at)


def _site(at):
    return at.session_state[ra.SITE_KEY]


def _noops(at):
    return [q for q in _site(at).no_advance_turns if q.get("outcome") == ra.NONADVANCING_CLARIFICATION_NOOP]


def _started(world, *orders):
    at = _sign_in(world, _account(world, "resident"))
    _begin(at)
    for text in orders:
        page._order(at, text)
    return at


def _alive(at):
    site = _site(at)
    assert not site.halted, site.halt_reason
    assert at.session_state["encounter_ended"] is not True and _pilot(at)["exit"] is None
    assert ra.verify_artifact(site.artifact())["complete"], ra.verify_artifact(site.artifact())["real_claims_problems"]


def _ne_rate(at):
    return float(dict(at.session_state["state"].get("family_state") or {}).get("norepinephrine") or 0.0)


# -- P3-540: the clarification flows ------------------------------------------------------------------------------------------------------------------------

def test_c1_an_incomplete_saline_order_is_held_on_the_same_minute_and_its_completion_runs(world):
    at = _started(world, ORDERS[0])
    minute, committed = int(at.session_state["state"]["sim_time"]), _site(at).minutes_committed
    _send(at, "Give normal saline.")
    _alive(at)
    assert int(at.session_state["state"]["sim_time"]) == minute and _site(at).minutes_committed == committed, "nothing committed, no time fabricated"
    assert at.session_state["pending_action"] and len(_noops(at)) == 1 and _noops(at)[0]["attached_to_committed_minute"] == minute
    assert "Confirm the bolus volume" in _screen(at)
    _send(at, "1000 mL over 30 minutes.")
    _alive(at)
    assert int(at.session_state["state"]["sim_time"]) > minute and len(_site(at).minutes_committed) == len(committed) + 1
    assert not at.session_state["pending_action"]


def test_c2_increase_norepinephrine_without_a_unit_is_held_and_the_explicit_order_runs(world):
    at = _started(world, ORDERS[0], ORDERS[1])
    assert _ne_rate(at) == 10.0
    _send(at, "Increase norepinephrine to 12.")
    _alive(at)
    assert _ne_rate(at) == 10.0 and len(_noops(at)) == 1, "a rate without a unit never runs"
    assert "Specify an explicit rate with its units" in _screen(at)
    _send(at, "12 mcg/min.")                                           # the reader asks for a complete order (FD-ORDER-01): still nothing runs, still on the minute
    _alive(at)
    assert _ne_rate(at) == 10.0
    _send(at, "Increase norepinephrine to 12 mcg/min. Reassess in 10 minutes.")
    _alive(at)
    assert _ne_rate(at) == 12.0 and "None of it was administered" in _screen(at)


def test_c3_restart_without_a_rate_is_held_and_never_reuses_the_earlier_rate(world):
    at = _started(world, ORDERS[0], ORDERS[1], "Stop norepinephrine. Reassess in 10 minutes.")
    assert _ne_rate(at) == 0.0
    _send(at, "Restart norepinephrine.")
    _alive(at)
    assert _ne_rate(at) == 0.0 and len(_noops(at)) == 1
    _send(at, "Restart norepinephrine at 8 mcg/min. Reassess in 10 minutes.")
    _alive(at)
    assert _ne_rate(at) == 8.0


def test_c4_a_map_target_never_becomes_a_dose_and_mutates_nothing(world):
    at = _started(world, ORDERS[0], ORDERS[1])
    state_before = json.dumps(at.session_state["state"], sort_keys=True, default=str)
    _send(at, "Titrate norepinephrine to MAP 65.")
    _alive(at)
    assert json.dumps(at.session_state["state"], sort_keys=True, default=str) == state_before, "the patient state is byte for byte the same"
    assert _ne_rate(at) == 10.0 and len(_noops(at)) == 1
    held = [row for row in _noops(at)[0]["held_orders"]]
    assert held and all(row["fate"] == "HELD_CLARIFICATION" for row in held)
    _send(at, "Increase norepinephrine to 14 mcg/min. Reassess in 10 minutes.")
    _alive(at)
    assert _ne_rate(at) == 14.0


def test_c5_consecutive_clarifications_are_each_a_noop_and_the_completion_still_runs(world):
    at = _started(world, ORDERS[0])
    minute = int(at.session_state["state"]["sim_time"])
    for text in ("Give normal saline.", "Give normal saline.", "more"):
        _send(at, text)
        _alive(at)
    assert int(at.session_state["state"]["sim_time"]) == minute and len(_noops(at)) == 3
    _send(at, "500 mL over 15 minutes.")
    _alive(at)
    assert int(at.session_state["state"]["sim_time"]) > minute


def test_c6_a_turn_mixing_a_complete_order_with_an_incomplete_one_runs_the_complete_one_and_holds_the_other(world):
    at = _started(world, ORDERS[0], ORDERS[1])
    minute = int(at.session_state["state"]["sim_time"])
    _send(at, "Give 500 mL normal saline over 15 minutes. Increase norepinephrine to 12. Reassess in 15 minutes. I expect the pressure to improve.")
    _alive(at)
    assert int(at.session_state["state"]["sim_time"]) > minute and _ne_rate(at) == 10.0, "the saline ran, the rate without a unit did not"
    _send(at, "Place a second large-bore IV. Increase norepinephrine to 12.")
    _alive(at)
    assert _ne_rate(at) == 10.0


def test_c7_an_order_the_authority_does_not_represent_still_fails_closed(world):
    at = _started(world, ORDERS[0])
    _send(at, "Give tranexamic acid 1 g IV over 10 minutes.")
    site = _site(at)
    assert site.halted and not site.halt_reason.startswith(ra.MINUTE_ALREADY_COMMITTED), site.halt_reason
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_AUTHORITY_STOP


# -- P3-541: the development boundary ---------------------------------------------------------------------------------------------------------------------

BOUNDARY_PHRASES = ("Call gastroenterology.", "Notify GI.", "Get the GI team.", "Scope him.", "Upper endoscopy please.", "IR for embolization.", "Take him to the OR.",
                    "Band the varices.", "Control the bleeding.", "He needs surgery.")


@pytest.mark.parametrize("text", BOUNDARY_PHRASES)
def test_c8_every_definitive_control_phrasing_ends_at_the_boundary_before_the_engine(world, text):
    at = _started(world, ORDERS[0])
    minute = int(at.session_state["state"]["sim_time"])
    _send(at, text)
    at.run()
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_DEFINITIVE_REQUEST, (text, _pilot(at))
    family = dict(at.session_state["state"].get("family_state") or {})
    assert not family.get("consultations") and family.get("endoscopy_at") is None, "nothing reached the engine"
    assert int(at.session_state["state"]["sim_time"]) == minute


def test_c9_the_structural_barrier_stops_a_definitive_consultation_even_when_every_word_reading_misses_it(world, monkeypatch):
    monkeypatch.setattr(gp, "definitive_intent", lambda orders, text=None: [])     # a mutant: every word-based reading misses
    monkeypatch.setattr(gp, "definitive_orders", lambda orders: [])
    at = _started(world, ORDERS[0])
    _send(at, "Call gastroenterology.")
    at.run()
    assert _pilot(at)["exit"] == gp.EXIT_DEFINITIVE_REQUEST
    assert not dict(at.session_state["state"].get("family_state") or {}).get("consultations"), "the consultation never reached the engine"


def test_c9b_a_consultation_that_is_not_definitive_still_runs(world):
    at = _started(world, ORDERS[0])
    _send(at, "Consult ICU.")
    _alive(at)
    assert [c["service"] for c in dict(at.session_state["state"].get("family_state") or {}).get("consultations") or []] == ["ICU"]


# -- P3-542: mental status ----------------------------------------------------------------------------------------------------------------------------------

def test_c10_once_norepinephrine_is_given_talk_mode_is_withheld_and_no_mental_status_word_is_shown(world):
    at = _started(world, ORDERS[0])
    page._mode(at, "Talk")
    assert any("Ask" in str(item.label) for item in at.text_input), "before norepinephrine the patient can be asked"
    page._order(at, ORDERS[1])
    page._mode(at, "Talk")
    assert not any("Ask" in str(item.label) for item in at.text_input) and gpu.TALK_WITHHELD.split(":")[0] in _screen(at)
    page._examine(at)
    _send(at, "Increase norepinephrine to 12 mcg/min. Reassess in 10 minutes.")
    screen = _screen(at)
    for word in MENTAL:
        assert f"{word};" not in screen and f"status: {word}" not in screen and f"Mental status: {word.lower()}" not in screen, word


# -- P3-545 / P3-550: robustness and failure injection ------------------------------------------------------------------------------------------------------

def test_c11_a_rerun_during_a_clarification_keeps_the_held_order_and_the_authority(world):
    at = _started(world, ORDERS[0])
    _send(at, "Give normal saline.")
    for _ in range(3):
        at.run()
        assert not at.exception
    _alive(at)
    assert at.session_state["pending_action"] and len(_noops(at)) == 1
    _send(at, "1000 mL over 30 minutes.")
    _alive(at)


def test_c12_a_new_session_during_a_clarification_records_the_open_encounter_interrupted_at_once(world):
    credentials = _account(world, "resident")
    first = _sign_in(world, credentials)
    _begin(first)
    page._order(first, ORDERS[0])
    _send(first, "Give normal saline.")
    eid = _pilot(first)["encounter_id"]
    again = _sign_in(world, credentials)                               # a refresh, a restart or a second tab: a new browser session never resumes
    assert "Begin the development pilot encounter" in _screen(again)
    assert _store(world).status(eid)["state"] == "INTERRUPTED", "the open encounter is closed in the record as soon as a new session opens the pilot"
    minute = int(first.session_state["state"]["sim_time"])
    first.run()                                                        # the old tab's next run: it ends before it can offer the held order again
    assert not first.exception
    assert first.session_state["encounter_ended"] is True and _pilot(first)["exit"] == gp.EXIT_CLOSED_IN_RECORD
    assert not [a for a in first.text_area if a.label == BOX], "no order can be written in the closed encounter"
    assert int(first.session_state["state"]["sim_time"]) == minute, "the held order never ran"


def test_c13_a_faculty_stop_during_a_clarification_ends_the_encounter_before_the_held_order_runs(world):
    at = _started(world, ORDERS[0])
    _send(at, "Give normal saline.")
    eid, minute = _pilot(at)["encounter_id"], int(at.session_state["state"]["sim_time"])
    _store(world).append_faculty(eid, gp.faculty_ref("faculty-dry-run"), "stop", {"why": "dry run during a clarification"})
    at.run()                                                           # the participant's next run: the stop is read before anything else
    assert not at.exception
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_FACULTY_STOP
    assert not [a for a in at.text_area if a.label == BOX], "the held order cannot be completed after the stop"
    assert int(at.session_state["state"]["sim_time"]) == minute, "the held order never ran"


def test_c14_the_faculty_replay_review_matches_after_clarification_noops(world):
    at = _started(world, ORDERS[0])
    _send(at, "Give normal saline.")
    _send(at, "1000 mL over 30 minutes.")
    _send(at, "Titrate norepinephrine to MAP 65.")
    eid = _pilot(at)["encounter_id"]
    next(item for item in at.button if "Complete Encounter" in item.label).click().run()
    finish = next((item for item in at.button if item.label == "Finish now"), None)
    if finish is not None:
        finish.click().run()
    at.run()
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_PARTICIPANT_FINISHED
    screen = _screen(at)
    assert "held for a question; not carried out" in screen, "the trace says what the simulator did with the held order"
    for token in INTERNALS:
        if token in ("score", "Score"):
            continue                                                   # the trace's own disclaimer says "it is not a score"; a score itself is pinned below
        assert token not in screen, token
    assert "not a score" in screen and "Score:" not in screen and "score:" not in screen
    review = gp.replay_review(_store(world), eid, gpu.layer())
    assert review["usable"] and set(review["checks"].values()) == {"MATCH"}, review
    artifact = _store(world).artifact(eid)
    assert [q["outcome"] for q in artifact["no_advance_turns"]].count(ra.NONADVANCING_CLARIFICATION_NOOP) == 2
    assert ra.clarification_noop_problems(artifact) == []


def test_c15_the_launcher_says_an_incomplete_order_is_held_and_how_to_complete_it(world):
    at = _sign_in(world, _account(world, "resident"))
    screen = _screen(at)
    assert "can end the development encounter early" not in screen.split("Other medications")[0]
    assert "holds it and asks what is missing" in screen and "Increase norepinephrine to 12 mcg/min" in screen
    for declared in ("ending the development encounter early", "nasogastric tube", "mg/min, mcg/kg/min", "ends the encounter at the development boundary"):
        assert declared in screen, declared


def test_c16_a_clarification_noop_the_store_cannot_write_is_withdrawn_and_the_experiment_stops(world, monkeypatch):
    import runtime_authority_store as ras
    at = _started(world, ORDERS[0])
    monkeypatch.setattr(ras, "persist", lambda artifact, environ=None: {"stored": False, "why": "injected: store unavailable"})
    _send(at, "Give normal saline.")
    at.run()
    site = _site(at)
    assert site.halted and ra.ARTIFACT_PERSISTENCE_FAILED in site.halt_reason, site.halt_reason
    assert not _noops(at), "a no-op that was never durable is not listed"
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_AUTHORITY_STOP
    assert not at.session_state["pending_action"], "the turn the store could not record was not applied"


def test_c17_a_tampered_and_resealed_noop_makes_the_faculty_replay_review_mismatch(world):
    at = _started(world, ORDERS[0])
    _send(at, "Give normal saline.")
    eid = _pilot(at)["encounter_id"]
    artifact = _site(at).artifact()
    tampered = json.loads(json.dumps(artifact, default=dict))                # the artifact holds read-only mappings; the stored form is plain JSON
    tampered["no_advance_turns"][-1]["proof"]["patient_state_unchanged"] = False
    body = {key: value for key, value in tampered.items() if key != "artifact_digest"}
    tampered["artifact_digest"] = ra.digest_of(body)                   # re-sealed: its own digest matches
    assert ra.verify_artifact(tampered)["digest_matches"] and not ra.verify_artifact(tampered)["complete"]

    class Store:
        def __init__(self, real):
            self.real = real

        def __getattr__(self, name):
            return getattr(self.real, name)

        def artifact(self, eid_):
            return tampered
    review = gp.replay_review(Store(_store(world)), eid, gpu.layer())
    assert review["checks"]["artifact_verifies"] == "MISMATCH" and not review["usable"], review



def _finish(at):
    next(item for item in at.button if "Complete Encounter" in item.label).click().run()
    finish = next((item for item in at.button if item.label == "Finish now"), None)
    if finish is not None:
        finish.click().run()
    at.run()
    assert not at.exception


# -- P3-552: the independent review's material findings, pinned on the real page ----------------------------------------------------------------------------

@pytest.mark.parametrize("text", ["Keep NPO.", "Monitor vitals every 5 minutes.", "Type and screen.", "Increase norepinephrine by 2 mcg/min.", "Hold antihypertensives."])
def test_c18_a_routine_order_that_acts_on_nothing_is_a_noop_and_the_encounter_goes_on(world, text):
    """Finding 1: these ended the encounter as UNSAFE_MUTATION although nothing changed. Nothing was done, the proof holds, and the encounter goes on."""
    at = _started(world, ORDERS[0], ORDERS[1])
    rate, minute = _ne_rate(at), int(at.session_state["state"]["sim_time"])
    _send(at, text)
    _alive(at)
    assert _ne_rate(at) == rate and int(at.session_state["state"]["sim_time"]) == minute and len(_noops(at)) == 1


@pytest.mark.parametrize("text", ["Place an NG tube.", "Give ondansetron 4 mg IV.", "Increase norepinephrine to 12 mg/min."])
def test_c19_what_the_development_model_does_not_represent_still_fails_closed_as_declared(world, text):
    at = _started(world, ORDERS[0], ORDERS[1])
    _send(at, text)
    at.run()
    site = _site(at)
    assert site.halted and at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_AUTHORITY_STOP, (text, site.halt_reason)
    assert _ne_rate(at) == 10.0, "nothing was given"
    if site.records[-1].get("nonadvancing"):
        assert site.records[-1]["nonadvancing"]["class"] != ra.UNSAFE_MUTATION or site.records[-1]["nonadvancing"]["proof"]["patient_state_unchanged"] is False, \
            "an order that changed nothing is never called a mutation"


@pytest.mark.parametrize("text", ["Hold off on GI for now.", "What is the GI plan?", "Check CBC with bands.", "Give 1 L normal saline over 15 minutes, GI bleed protocol.",
                                  "If he rebleeds, call GI."])
def test_c20_what_is_not_a_request_for_definitive_control_never_ends_the_encounter_and_the_trace_says_so(world, text):
    """Finding 2: negations, questions, a word inside a test, a diagnosis and a conditional plan are not a request; the encounter goes on and, after it, the participant's
    trace verifies, marks no request for definitive control and the faculty replay review matches (finding 4)."""
    at = _started(world, ORDERS[0])
    _send(at, text)
    _alive(at)
    assert _pilot(at)["exit"] is None and not dict(at.session_state["state"].get("family_state") or {}).get("consultations")
    eid = _pilot(at)["encounter_id"]
    _finish(at)
    screen = _screen(at)
    assert "Your management trace" in screen and gp.TRACE_WITHHELD.split(".")[0] not in screen
    assert gp.DEFINITIVE_MESSAGE.split(".")[0] not in screen and "request for definitive control" not in screen.lower().split("ends the encounter at the development boundary")[-1]
    review = gp.replay_review(_store(world), eid, gpu.layer())
    assert review["usable"], review


def test_c21_a_boundary_only_the_pilot_reads_says_the_turn_was_recorded_and_not_carried_out(world):
    at = _started(world, ORDERS[0])
    _send(at, "Get the GI team to scope him.")
    at.run()
    assert _pilot(at)["exit"] == gp.EXIT_DEFINITIVE_REQUEST
    screen = _screen(at)
    assert gp.FATE_WORDS["NOT_EXECUTED_BOUNDARY"] in screen
    assert gp.FATE_WORDS["RECORDED_NOT_MODELLED"] not in screen.split("Your management trace")[-1]


# -- P3-550: failure injection while an order is held for clarification ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("flag", [ra.TONE_FLAG, ra.AUTHORITY_FLAG])
def test_c22_a_configuration_withdrawn_while_an_order_is_held_closes_the_encounter_and_it_never_resumes(world, monkeypatch, flag):
    """The pilot gate refuses the page (nothing runs, no return to the earlier engine), the record ENDS the open encounter at once (AUTHORITY_UNAVAILABLE) instead of
    leaving it ACTIVE, and when the configuration comes back the session's encounter ends before its held order can run."""
    import os
    at = _started(world, ORDERS[0], ORDERS[1])
    _send(at, "Give normal saline.")
    _alive(at)
    eid, minute = _pilot(at)["encounter_id"], int(at.session_state["state"]["sim_time"])
    value = os.environ[flag]
    monkeypatch.delenv(flag)
    at.run()
    assert "DEVELOPMENT PILOT UNAVAILABLE" in _screen(at) and not [a for a in at.text_area if a.label == BOX]
    status = _store(world).status(eid)
    assert status["state"] == "ENDED" and status["exit"] == gp.EXIT_AUTHORITY_UNAVAILABLE and not status["problems"], status
    monkeypatch.setenv(flag, value)                                    # the configuration comes back: the encounter does not
    at.run()
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_CLOSED_IN_RECORD, _pilot(at)
    assert not [a for a in at.text_area if a.label == BOX]
    assert int(at.session_state["state"]["sim_time"]) == minute and at.session_state["pending_action"], "the held order never ran"


def test_c23_a_pressure_computed_under_another_snapshot_while_an_order_is_held_is_a_hard_failure_never_a_noop(world, monkeypatch):
    """The configuration check runs BEFORE the no-op is judged: a clarification is never a way around it."""
    at = _started(world, ORDERS[0], ORDERS[1])
    _send(at, "Give normal saline.")
    _alive(at)
    minute = int(at.session_state["state"]["sim_time"])
    monkeypatch.setattr(ra.AuthoritySite, "_configuration_mismatch", lambda self, session: "injected: the session computed another snapshot's pressure")
    _send(at, "Increase norepinephrine to 12.")
    at.run()
    site = _site(at)
    assert site.halted and site.halt_reason.startswith(ra.PRESSURE_CONFIGURATION_MISMATCH), site.halt_reason
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_AUTHORITY_STOP
    assert int(at.session_state["state"]["sim_time"]) == minute and _ne_rate(at) == 10.0
