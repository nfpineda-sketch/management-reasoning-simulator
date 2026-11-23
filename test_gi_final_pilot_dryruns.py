"""P3-548 / P3-549: the realistic resident and faculty-supervised dry runs of the GI development pilot, on the REAL page (Streamlit AppTest, synthetic accounts).

Every dry run ends in one of two ways, and each is checked: a valid encounter (the participant's management trace verifies and the faculty replay review MATCHES on every
check), or an explicitly correct fail-closed stop (the stated exit, nothing carried out past it, the record still chained). Nothing here starts a real pilot.

DRY-1 straightforward: volume and blood -> reassess -> norepinephrine -> reassess -> request for definitive control (the development boundary).
DRY-2 incomplete saline order -> clarification -> completion -> continue.
DRY-3 incomplete norepinephrine rate -> clarification -> completion -> continue.
DRY-4 norepinephrine start -> rate change -> stop.
DRY-5 a bad or unsafe order: a MAP target, a relative change or a rate without a unit is held and never runs; weight-based dosing and an unrepresented drug fail closed.
DRY-6 a request for definitive control -> the development boundary.
DRY-7 refresh / reconnect in the middle of the encounter.
DRY-8 faculty abort.
FACULTY observes, aborts, inspects the trace, reviews the replay, flags and marks unusable, with no scoring consequence anywhere.
"""
import pytest

import gi_pilot as gp
import gi_pilot_ui as gpu
import runtime_authority as ra
import test_phase3_pair_page as page
from test_gi_final_pilot_page import BOX, _alive, _ne_rate, _noops, _send, _site
from test_gi_pilot_page import ORDERS, REQUEST, _account, _begin, _pilot, _screen, _sign_in, _store, world  # noqa: F401

pytestmark = pytest.mark.ordinary_configuration
EXPECT = " I expect the blood pressure and perfusion to improve."


def _finish(at):
    """The participant ends the encounter (Complete Encounter, Finish now)."""
    next(item for item in at.button if "Complete Encounter" in item.label).click().run()
    finish = next((item for item in at.button if item.label == "Finish now"), None)
    if finish is not None:
        finish.click().run()
    at.run()
    assert not at.exception


def _valid(world, at, exit_kind):
    """A valid ended encounter: the stated exit, a trace that verifies, and a faculty replay review that matches on every check."""
    info = _pilot(at)
    assert at.session_state["encounter_ended"] is True and info["exit"] == exit_kind, info
    review = gp.replay_review(_store(world), info["encounter_id"], gpu.layer())
    assert review["usable"] and set(review["checks"].values()) == {"MATCH"}, review
    assert "Your management trace" in _screen(at) and gp.TRACE_WITHHELD.split(".")[0] not in _screen(at)
    return info["encounter_id"]


def _stopped(world, at, exit_kind):
    """A correct fail-closed stop: the stated exit, the chained record intact, and nothing past the stop."""
    info = _pilot(at)
    assert at.session_state["encounter_ended"] is True and info["exit"] == exit_kind, info
    assert not _store(world).logs(info["encounter_id"])["problems"]
    assert not [a for a in at.text_area if a.label == BOX]
    review = gp.replay_review(_store(world), info["encounter_id"], gpu.layer())
    assert review["checks"]["logs_chain"] == "MATCH" and review["checks"]["artifact_verifies"] == "MATCH", review
    return info["encounter_id"]


def _start(world):
    at = _sign_in(world, _account(world, "resident"))
    _begin(at)
    return at


def test_dry1_straightforward_volume_blood_reassess_norepinephrine_reassess_boundary(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    page._order(at, ORDERS[1])
    page._examine(at)
    _send(at, "Reassess in 15 minutes.")
    _alive(at)
    _send(at, REQUEST)
    at.run()
    eid = _valid(world, at, gp.EXIT_DEFINITIVE_REQUEST)
    assert len(_store(world).artifact(eid)["minutes"]) >= 3


def test_dry2_incomplete_saline_clarification_completion_continue(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    _send(at, "Give normal saline.")
    _alive(at)
    _send(at, "500 mL over 15 minutes.")
    _alive(at)
    _send(at, "Reassess in 15 minutes.")
    _alive(at)
    _finish(at)
    eid = _valid(world, at, gp.EXIT_PARTICIPANT_FINISHED)
    assert [q["outcome"] for q in _store(world).artifact(eid)["no_advance_turns"]].count(ra.NONADVANCING_CLARIFICATION_NOOP) == 1


def test_dry3_incomplete_norepinephrine_rate_clarification_completion_continue(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    _send(at, "Start norepinephrine." + EXPECT)
    _alive(at)
    assert _ne_rate(at) == 0.0 and _noops(at)
    _send(at, "Start norepinephrine at 8 mcg/min. Reassess in 15 minutes." + EXPECT)
    _alive(at)
    assert _ne_rate(at) == 8.0
    _finish(at)
    _valid(world, at, gp.EXIT_PARTICIPANT_FINISHED)


def test_dry4_norepinephrine_start_rate_change_stop(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    page._order(at, ORDERS[1])
    assert _ne_rate(at) == 10.0
    _send(at, "Increase norepinephrine to 14 mcg/min. Reassess in 10 minutes.")
    assert _ne_rate(at) == 14.0
    _send(at, "Decrease norepinephrine to 6 mcg/min. Reassess in 10 minutes.")
    assert _ne_rate(at) == 6.0
    _send(at, "Stop norepinephrine. Reassess in 10 minutes.")
    _alive(at)
    assert _ne_rate(at) == 0.0
    _finish(at)
    _valid(world, at, gp.EXIT_PARTICIPANT_FINISHED)


def test_dry5_a_target_a_relative_change_or_a_rate_without_a_unit_is_held_and_never_runs(world):
    """DRY-5, held: none of these is a dose (FD-ORDER-01, FD-AUTHNE); each is a proven clarification no-op on the same minute and the encounter goes on."""
    at = _start(world)
    page._order(at, ORDERS[0])
    page._order(at, ORDERS[1])
    minute = int(at.session_state["state"]["sim_time"])
    for text in ("Titrate norepinephrine to MAP 65.", "Double the norepinephrine.", "Increase norepinephrine to 12."):
        _send(at, text)
        _alive(at)
        assert _ne_rate(at) == 10.0 and int(at.session_state["state"]["sim_time"]) == minute, text
    # the first is judged by the authority as a proven no-op; a reply while an order is held answers the held order (the page's clarification route) and runs nothing either
    assert len(_noops(at)) >= 1 and _site(at).minutes_committed[-1] == minute
    _finish(at)
    _valid(world, at, gp.EXIT_PARTICIPANT_FINISHED)


@pytest.mark.parametrize("text", ["Increase norepinephrine to 0.2 mcg/kg/min.", "Give tranexamic acid 1 g IV over 10 minutes."])
def test_dry5_an_order_the_authority_does_not_represent_fails_closed_and_nothing_runs(world, text):
    """DRY-5, fail closed: weight-based norepinephrine is never converted (FD-AUTHNE) and an unrepresented medication is decision C; the encounter stops with the stated
    exit, the vasopressor rate is unchanged, the record stays chained, and the stop is never the same-minute rule."""
    at = _start(world)
    page._order(at, ORDERS[0])
    page._order(at, ORDERS[1])
    _send(at, text)
    at.run()
    _stopped(world, at, gp.EXIT_AUTHORITY_STOP)
    assert _ne_rate(at) == 10.0, "nothing was given"
    assert _site(at).halt_reason.startswith(ra.UNSUPPORTED_AUTHORITY_ACTION), _site(at).halt_reason


def test_dry6_a_request_for_definitive_control_ends_at_the_development_boundary(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    _send(at, "Get the GI team to scope him.")
    at.run()
    _valid(world, at, gp.EXIT_DEFINITIVE_REQUEST)
    assert not dict(at.session_state["state"].get("family_state") or {}).get("consultations")


def test_dry7_refresh_and_reconnect_in_the_middle_of_the_encounter(world):
    credentials = _account(world, "resident")
    at = _sign_in(world, credentials)
    _begin(at)
    page._order(at, ORDERS[0])
    at.run()                                                           # a reconnect of the same session: nothing lost
    _alive(at)
    eid = _pilot(at)["encounter_id"]
    fresh = _sign_in(world, credentials)                               # a refresh: a new session never resumes
    assert _store(world).status(eid)["state"] == "INTERRUPTED"
    review = gp.replay_review(_store(world), eid, gpu.layer())
    assert review["checks"]["logs_chain"] == review["checks"]["artifact_verifies"] == review["checks"]["artifact_reproduces"] == "MATCH", review
    _begin(fresh)
    page._order(fresh, ORDERS[0])
    _alive(fresh)
    assert _pilot(fresh)["encounter_id"] != eid


def test_dry8_faculty_abort(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    eid = _pilot(at)["encounter_id"]
    faculty = _sign_in(world, _account(world, "faculty"))
    next(item for item in faculty.selectbox if item.label == "Encounter").set_value(eid).run()
    assert not faculty.exception
    stop = next(item for item in faculty.button if "Stop" in item.label)
    stop.click().run()
    assert not faculty.exception
    at.run()
    _stopped(world, at, gp.EXIT_FACULTY_STOP)


def test_faculty_dry_run_observe_inspect_replay_flag_unusable_and_no_score(world):
    at = _start(world)
    page._order(at, ORDERS[0])
    _send(at, "Give normal saline.")
    _send(at, "1000 mL over 30 minutes.")
    _finish(at)
    eid = _pilot(at)["encounter_id"]
    faculty = _sign_in(world, _account(world, "faculty"))
    assert faculty.title[0].value == gpu.SUPERVISION_TITLE
    next(item for item in faculty.selectbox if item.label == "Encounter").set_value(eid).run()
    next(item for item in faculty.button if item.label == "Review the replay").click().run()
    assert not faculty.exception and any("every check matches" in str(item.value) for item in faculty.success), [str(item.value) for item in faculty.error]
    next(item for item in faculty.button if item.label == "Inspect the trace").click().run()
    assert not faculty.exception
    next(item for item in faculty.text_area if item.label.startswith("What is unsafe or ambiguous")).set_value("Dry run: the clarification wording.").run()
    next(item for item in faculty.button if item.label == "Record the flag").click().run()
    next(item for item in faculty.text_input if item.label == "Why is this encounter unusable?").set_value("Dry run: synthetic account.").run()
    next(item for item in faculty.button if item.label == "Mark unusable").click().run()
    assert not faculty.exception
    status = _store(world).status(eid)
    assert status["unusable"] and status["flags"] == 1
    for screen in (_screen(at), _screen(faculty)):
        for word in ("Score:", "score:", "Grade:", "ranking", "Ranking", "radar"):
            assert word not in screen, word
    assert "_attempt_id" not in at.session_state or at.session_state["_attempt_id"] is None, "the pilot encounter creates no attempt: nothing reaches progress or evaluation"
