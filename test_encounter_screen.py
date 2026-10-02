"""The clinical encounter's screen (UX of the clinical encounter, faculty instruction of 2026-10-02).

Presentation only: the patient on the left, the information and the writing area on the
right, and the sidebar replaced by the room's menu. What the instruction requires of it:

* one mode is selected, four views are drawn, and consulting them changes nothing (section 4);
* the four reasoning fields keep their trigger, questions, validation and record; they are in
  view while they wait and leave no transcript in Evolution (section 5);
* Evolution repeats neither the resident's words nor the room's messages about an order, and
  drops no entry it cannot classify (section 6);
* a question an order waits on stays in view until it is answered (section 7);
* "View ECG" opens exactly the recording its notice announced, without asking for another or
  moving the clock (section 8);
* a resident sees no development control and no finding that was not obtained (sections 3, 10);
* during the encounter the sidebar is not drawn, and its controls are in the menu (section 11);
* the review that follows the close keeps what it showed above the chart.
"""
import time
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import encounter_screen as screen
from account_store import AccountStore

APP = str(Path(__file__).with_name("app.py"))
FOUR_FIELDS = ("What do you think is going on?", "What are you going to do?",
               "What do you expect to happen, or what are you trying to clarify?", "What will you check, and when?")


def widget(elements, label):
    return next(item for item in elements if item.label == label)


def send(at, text):
    widget(at.text_area, "Enter your clinical reasoning and/or actions").set_value(text)
    widget(at.button, "Send").click().run()
    assert not at.exception


def record(at):
    """What the encounter holds: the views must never change it."""
    return deepcopy((at.session_state["state"], at.session_state["events"], at.session_state["management_trace"]))


def shown_text(at):
    return " ".join(str(item.value) for kind in ("markdown", "caption", "warning", "info")
                    for item in getattr(at, kind))


def blocks(node):
    found = [node]
    for child in (getattr(node, "children", None) or {}).values():
        found += blocks(child)
    return found


@pytest.fixture
def room(tmp_path, monkeypatch):
    """A real bank case (acs_61m_posterior) through the real page, offline, for a given role."""
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    store = AccountStore(url, allow_sqlite=True)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "acs_61m_posterior")):
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import curriculum_runtime
    monkeypatch.setattr(curriculum_runtime, "assign_challenge", lambda *args, **kwargs: {
        "challenge_id": "R2-02", "reason": "test", "assignment_seed": 17,
        "competence_decision": "Not assessed automatically"})
    from resident_profile import ProfileStore

    def opening(role="resident", begin=True):
        with store._transaction(write=True) as connection:
            user_id = uuid.uuid4().hex
            store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                           (user_id, f"{role}_{user_id[:6]}", "unused-fixture-hash", role,
                            2 if role == "resident" else None, int(time.time())))
            token = store._new_session(connection, user_id)
        ProfileStore(store).decline(token)
        at = AppTest.from_file(APP, default_timeout=120)
        at.session_state["_account_token"] = token
        at.run()
        assert not at.exception
        if begin:
            if role != "resident":                  # staff choose the challenge in their sandbox
                widget(at.selectbox, "Management challenge").set_value("R2-02").run()
            widget(at.button, "Begin Encounter").click().run()
            assert not at.exception
            assert at.session_state["state"]["encounter_spec"]["variant_id"] == "acs_61m_posterior"
        return at
    return opening


# -- the page ---------------------------------------------------------------------------------------------------
def test_the_sidebar_is_not_drawn_in_the_room_and_its_controls_are_in_the_menu(room):
    at = room(begin=False)
    assert at.sidebar.children                      # the dashboard keeps its sidebar
    widget(at.button, "Begin Encounter").click().run()
    assert not at.exception and not at.sidebar.children
    menu = [block for block in blocks(at.main) if getattr(block, "type", None) == "popover"]
    assert len(menu) == 1
    inside = {item.label for item in blocks(menu[0]) if getattr(item, "type", None) == "button"}
    assert {"Sign out", "Save & return to dashboard", "End this attempt without completing review"} <= inside
    language = next(item for item in at.selectbox if item.key == "presentation_language")
    assert language.disabled                        # fixed during the encounter, as it was


def test_one_mode_is_selected_and_the_four_views_are_drawn(room):
    at = room()
    assert [tab.label for tab in at.tabs][:4] == ["Evolution", "History & Exam", "Results", "Orders"]
    mode = widget(at.radio, "Encounter")
    assert mode.options == ["Talk", "Examine", "Tests", "Treat"] and mode.value == "Treat"
    assert "Simulated time · 0 min" in shown_text(at)


def test_the_four_fields_wait_in_view_and_leave_no_transcript(room):
    at = room()
    send(at, "Aspirin 300 mg PO now.")
    assert at.session_state["pending_reasoning"]
    assert set(FOUR_FIELDS) <= {item.label for item in at.text_area}
    held = widget(at.text_area, "What are you going to do?")
    assert held.disabled and "aspirin" in held.value.lower()
    assert widget(at.number_input, "I will check in… minutes").value == 5
    # Validation unchanged: a missing answer keeps the form and what was written.
    widget(at.text_area, "What do you think is going on?").set_value("An anterior occlusion pattern.")
    widget(at.button, "Complete reasoning & execute held order").click().run()
    assert not at.exception and at.session_state["pending_reasoning"]
    # What was written stays, as the held order keeps it (without its final stop).
    assert widget(at.text_area, "What do you think is going on?").value.rstrip(".") == "An anterior occlusion pattern"
    assert not at.session_state["management_trace"]
    widget(at.text_area, FOUR_FIELDS[2]).set_value("Less platelet aggregation.")
    widget(at.text_area, FOUR_FIELDS[3]).set_value("Pain, ECG and BP in 10 minutes.")
    widget(at.button, "Complete reasoning & execute held order").click().run()
    assert not at.exception and not at.session_state["pending_reasoning"]
    assert not set(FOUR_FIELDS) & {item.label for item in at.text_area}
    # Recorded in full, and not repeated as a transcript in Evolution.
    completion = next(event for event in at.session_state["events"] if event["kind"] == "reasoning_completion")
    assert at.session_state["management_trace"][-1]["execution_status"] == "executed"
    evolution = " ".join(item.value for item in at.tabs[0].markdown)
    assert completion["text"] not in evolution and "REASONING COMPLETION" not in evolution
    # The order's outcome is said beside the writing area, from the record.
    assert "Action: " in shown_text(at)


def test_view_ecg_opens_the_recording_its_notice_announced_and_changes_nothing(room):
    from ecg12 import render_ecg_svg
    at = room()
    widget(at.button, "ECG").click().run()
    send(at, "Reassess in 5 minutes.")
    assert at.session_state["state"]["sim_time"] >= 5
    send(at, "Repeat 12-lead ECG now.")
    recordings = at.session_state["state"]["diagnostics"]["ecg"]
    assert len(recordings) == 2 and recordings[0]["recording_id"] != recordings[1]["recording_id"]
    widget(at.radio, "Encounter").set_value("Tests").run()
    before = record(at)
    for position, recording in ((1, recordings[0]), (0, recordings[1])):   # Evolution is newest first
        buttons = [item for item in at.tabs[0].button if item.label == "View ECG"]
        assert len(buttons) == 2
        buttons[position].click().run()
        assert not at.exception
        shown = next(item.value for item in at.markdown if 'aria-label="12-lead simulated ECG' in item.value)
        assert shown == "".join(line.strip() for line in render_ecg_svg(recording).splitlines())
        assert record(at) == before                 # no study asked for, no event, no minute
        assert widget(at.radio, "Encounter").value == "Tests"
    assert [item.label for item in at.tabs[2].button].count("View ECG") == 2   # and from Results


def test_a_question_an_order_waits_on_stays_in_view(room):
    at = room()
    send(at, "I think this is ACS with ongoing pain. Give morphine IV; I expect less pain; "
             "I will reassess pain and BP in 10 minutes.")
    question = "Please specify or confirm the morphine dose in milligrams."
    assert at.session_state["pending_action"]
    assert any(question in item.value for item in at.warning)
    # A question to the patient in between does not take it out of view.
    widget(at.radio, "Encounter").set_value("Talk").run()
    widget(at.text_input, "Ask the patient").set_value("Do you have any allergies?")
    widget(at.button, "Ask").click().run()
    assert not at.exception and at.session_state["pending_action"]
    assert any(question in item.value for item in at.warning)
    # The order is said as the record says it: waiting on its question, not dropped.
    assert any("Status: clarification required" in item.value for item in at.tabs[3].warning)
    assert any("Status: clarification required" in str(item.value) for item in at.markdown)
    assert not any("Status: not executed" in str(item.value) for item in at.markdown)


def test_a_resident_sees_no_development_control_and_no_finding_not_obtained(room):
    from family_engine import current_findings
    at = room()
    offered = {item.label for item in at.button} | {item.label for item in at.expander}
    assert not {"Image issue details", "Retry patient image"} & offered
    assert not any("Developer" in label for label in offered)
    # The chart's live panels read the current state without an examination; they are gone.
    lungs = current_findings(at.session_state["state"])["Respiratory"]
    assert lungs not in shown_text(at)
    assert not any(str(item.value).startswith("CRT:") for item in at.markdown)
    widget(at.radio, "Encounter").set_value("Examine").run()
    widget(at.selectbox, "Examine").set_value("Respiratory").run()
    widget(at.button, "Examine patient").click().run()
    assert lungs in " ".join(item.value for item in at.tabs[1].markdown)   # once examined, at its minute


def test_staff_keep_their_development_controls(room):
    at = room("faculty")
    assert any(item.label == "Developer: Management Trace" for item in at.expander)


def test_an_order_completed_in_free_text_is_said_with_what_it_did(room):
    at = room()
    send(at, "Aspirin 300 mg PO now.")
    assert at.session_state["pending_reasoning"]
    send(at, "I think this is an acute coronary syndrome. I expect less platelet aggregation and less pain. "
             "I will reassess pain, ECG and BP in 10 minutes.")
    assert not at.session_state["pending_reasoning"]
    assert any("Action: Aspirin 300 mg PO" in str(item.value) for item in at.markdown)


def test_the_strip_of_pending_studies_says_no_minute_the_room_has_not_said():
    # A family engine says when a result is due only when the resident asks to review it.
    family = [{"diagnostic": "troponin", "available_at_min": 29}]
    chart = {"pending_investigations": [{"diagnostic_type": "lactate", "available_at_min": 12}]}
    assert screen.pending_studies(chart, family) == [("troponin", None), ("lactate", 12)]


def test_the_review_after_the_close_keeps_what_it_showed_above_the_chart(room):
    at = room()
    widget(at.button, "ECG").click().run()
    send(at, "I think this is ACS. Give aspirin 300 mg PO; I expect less thrombosis; "
             "I will reassess pain and BP in 10 minutes.")
    widget(at.button, "Complete Encounter & Begin Review").click().run()
    if any(item.label == "Finish now" for item in at.button):
        widget(at.button, "Finish now").click().run()
    assert not at.exception and at.session_state["encounter_ended"]
    assert at.sidebar.children                      # the sidebar is back once the encounter is over
    [latest] = [item for item in at.expander if item.label == "Latest response"]
    said = " ".join(str(getattr(item, "value", "")) for item in blocks(latest))
    assert "After aspirin" in said and "I think this is ACS" not in said
    labels = {item.label for item in at.expander}
    assert {"ECG recordings", "Clinical chart · examination · results · treatment record"} <= labels
    assert not {"Image issue details", "Retry patient image"} & {item.label for item in at.button}


# -- what each view shows ---------------------------------------------------------------------------------------
EVENTS = [
    {"kind": "presentation", "time": 0, "text": "Arrival."},
    {"kind": "you", "time": 0, "text": "What brought you in?"},
    {"kind": "patient_history", "time": 1, "text": "Chest pain."},
    {"kind": "you", "time": 1, "text": "Examine: Breathing"},
    {"kind": "examination", "time": 2, "text": "Lungs clear."},
    {"kind": "you", "time": 2, "text": "Aspirin now and examine the chest."},
    {"kind": "examination", "time": 3, "text": "No added sounds."},
    {"kind": "clarification", "time": 3, "text": "A question."},
    {"kind": "reasoning_completion", "time": 3, "text": "Fields."},
    {"kind": "reasoning_note", "time": 3, "text": "A note."},
    {"kind": "clinical_update", "time": 5, "text": "After aspirin, BP 120/80."},
    {"kind": "prototype", "time": 5, "text": "Not executed in this build."},
    {"kind": "diagnostic", "time": 5, "text": "12-lead ECG acquired. Available in ECG recordings."},
    {"kind": "order_cancelled", "time": 6, "text": "Pending orders cancelled."},
    {"kind": "a_kind_not_yet_known", "time": 7, "text": "Something new."},
]


def test_evolution_is_the_patient_s_course_newest_first_and_drops_nothing_unknown():
    kinds = [event["kind"] for _, event in screen.evolution(EVENTS)]
    assert kinds == ["a_kind_not_yet_known", "diagnostic", "clinical_update", "examination", "examination",
                     "patient_history", "presentation"]
    assert not set(kinds) & screen.EXCHANGE_KINDS


def test_history_and_exam_keep_each_question_and_never_repeat_an_order():
    rows = [(event["text"], asked) for _, event, asked in screen.history_and_exam(EVENTS)]
    assert rows == [("No added sounds.", None), ("Lungs clear.", "Examine: Breathing"),
                    ("Chest pain.", "What brought you in?"), ("Arrival.", None)]


def test_an_ecg_notice_opens_its_own_recording_only_when_that_is_certain():
    events = [{"kind": "diagnostic", "time": 0, "text": "12-lead ECG acquired. Available in ECG recordings."},
              {"kind": "diagnostic_result", "time": 9,
               "text": "ECG: Performed at minute 8 · 12-lead tracing available in ECG recordings at the bedside."}]
    recordings = [{"acquired_at_minutes": 0, "status": "available"},
                  {"acquired_at_minutes": 8, "time_min": 9, "status": "available"}]
    assert screen.ecg_notices(events, recordings) == {0: 0, 1: 1}
    assert screen.ecg_notices(events, recordings[:1]) == {}                    # a recording unaccounted for
    assert screen.ecg_notices(events, [recordings[1], recordings[0]]) == {}    # announced before it existed
    assert not screen.viewable({"status": "unavailable"})


def test_an_order_is_shown_with_its_own_messages_and_a_cancellation_on_its_own():
    trace = [
        {"execution_status": "information", "state_before": {"encounter_event_count": 3},
         "state_after": {"encounter_event_count": 3}},
        {"execution_status": "executed", "state_before": {"encounter_event_count": 6},
         "state_after": {"encounter_event_count": 13}},
    ]
    rows = screen.order_rows(trace, EVENTS)
    assert [row["row"] for row in rows] == ["message", "order"]
    assert rows[0]["event"]["kind"] == "order_cancelled"
    assert [event["kind"] for _, event in rows[1]["messages"]] == ["clarification", "reasoning_note", "prototype"]
    start, messages = screen.latest_exchange(EVENTS)
    assert start == 8 and [event["kind"] for _, event in messages] == ["reasoning_note", "prototype", "order_cancelled"]


HELD = "**ORDER HELD — REASONING REQUIRED**\n\nI understood: aspirin."


def test_an_order_completed_after_it_was_held_keeps_its_answer_and_its_messages():
    # The room removes its prompt for the held order after the count was written, so the
    # count runs one ahead (free text, or a facilitator's override): the order is still the
    # resident's latest entry before it.
    events = [{"kind": "presentation", "time": 0, "text": "Arrival."},
              {"kind": "you", "time": 0, "text": "Aspirin 300 mg PO now."},
              {"kind": "you", "time": 0, "text": "execute without complete reasoning"},
              {"kind": "prototype", "time": 0, "text": "Facilitator override accepted."},
              {"kind": "clinical_update", "time": 10, "text": "After aspirin 300 mg PO administered, BP 132/80."}]
    trace = [{"execution_status": "executed", "learner_input": "Aspirin 300 mg PO now.\n\nOverride",
              "state_before": {"encounter_event_count": 4}, "state_after": {"encounter_event_count": 5}}]
    assert screen.latest_order(trace, events) is trace[0]
    [row] = screen.order_rows(trace, events)
    assert row["row"] == "order" and [position for position, _ in row["messages"]] == [3]


def test_an_order_the_record_holds_no_entry_for_is_shown_with_what_became_of_it():
    cancelled = {"kind": "order_cancelled", "time": 5, "text": "Pending orders cancelled before execution."}
    # Held, then cancelled: its words and the cancellation, once.
    events = [{"kind": "presentation", "time": 0, "text": "Arrival."},
              {"kind": "you", "time": 5, "text": "Give morphine."}, cancelled]
    [row] = screen.order_rows([], events)
    assert row["row"] == "unrecorded" and row["event"]["text"] == "Give morphine."
    assert [event for _, event in row["messages"]] == [cancelled]
    # Still held: its prompt is the room's, said by the held order's own block and form.
    held = [events[0], events[1], {"kind": "clarification", "time": 5, "text": HELD}]
    assert screen.order_rows([], held) == []
    # A message about no order at all is a row of its own.
    alone = [events[0], {"kind": "clarification", "time": 6, "text": "There are no pending orders to cancel."}]
    assert [row["row"] for row in screen.order_rows([], alone)] == ["message"]
    # A held order discarded to run a new one is said once, with the new order.
    events = [events[0], {"kind": "you", "time": 2, "text": "Give morphine IV."},
              {"kind": "clarification", "time": 2, "text": "Please specify the morphine dose."},
              {"kind": "you", "time": 3, "text": "Troponin now."},
              {"kind": "order_cancelled", "time": 3, "text": "The held order was discarded to run this one."}]
    trace = [{"execution_status": "clarification_required", "learner_input": "Give morphine IV.",
              "state_before": {"encounter_event_count": 2}, "state_after": {"encounter_event_count": 3}},
             {"execution_status": "executed", "learner_input": "Troponin now.",
              "state_before": {"encounter_event_count": 4}, "state_after": {"encounter_event_count": 5}}]
    rows = screen.order_rows(trace, events)
    assert [row["row"] for row in rows] == ["order", "order"]
    assert [position for row in rows for position, _ in row["messages"]] == [4, 2]


def test_an_order_that_did_not_run_is_said_with_the_record_s_own_status():
    import report_language
    said = {status: screen.order_status({"execution_status": status}) for status in (
        "executed", "clarification_required", "terminal_locked", "not_executed", "deferred")}
    assert said == {"executed": None, "clarification_required": "clarification required",
                    "terminal_locked": "not executed", "not_executed": "not executed", "deferred": "Pending"}
    # Each status has its approved Spanish.
    assert all(report_language.t(words, "es") != words for words in said.values() if words)


def test_the_screen_s_words_are_the_ones_the_instruction_gave_in_both_languages():
    import report_language
    assert {word: report_language.t(word, "es") for word in (
        "Evolution", "History & Exam", "Results", "Orders", "Send", "Simulated time", "Menu", "View ECG")} == {
        "Evolution": "Evolución", "History & Exam": "Historia y examen", "Results": "Resultados",
        "Orders": "Indicaciones", "Send": "Enviar", "Simulated time": "Tiempo simulado", "Menu": "Menú",
        "View ECG": "Ver ECG"}
    assert screen.minutes(14) == "14 min" and screen.minutes(None) == "0 min"
