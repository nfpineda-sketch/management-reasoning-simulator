"""The reported mixed order, driven through the resident's own submit path.

"patient in shock. Give 1000 NS, start oxygen 4l/m nasal cannula. POCUS, VBG,
lactate need to improve oxygenation and perfusion. Reassess in 10 min, hr,bp, O2"

The earlier encounter lost the treatments when one study was unavailable and
then executed only the study. These checks pin the whole turn: quantities and
units, device and flow, three separate investigations, venous rather than
arterial gases, one explicit time advance, what was actually infused as opposed
to ordered, and a trace that keeps the resident's own words.

No paid calls: the author client is a local stub.
"""
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from test_problem_launch import install_author

APP = str(Path(__file__).with_name("app.py"))
ORDER = ("patient in shock. Give 1000 NS, start oxygen 4l/m nasal cannula. "
         "POCUS, VBG, lactate need to improve oxygenation and perfusion. "
         "Reassess in 10 min, hr,bp, O2")


@pytest.fixture
def encounter(tmp_path, monkeypatch):
    from account_store import AccountStore, hash_password
    install_author(monkeypatch)
    url = "sqlite:///" + str(tmp_path / "mixed-order.sqlite3")
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("teacher", hash_password("local-test-password"))
    teacher = store.authenticate("teacher", "local-test-password")
    invite = store.create_invite(teacher, "resident", 1)
    token = store.register("mixed-order-resident", "local-resident-password", invite)
    app = AppTest.from_file(APP, default_timeout=120)
    app.session_state["_account_token"] = token
    app.run()
    assert not app.exception
    next(b for b in app.button if b.label == "Begin Encounter").click().run()
    assert not app.exception
    return app


def submit(app, text):
    app.text_area[0].set_value(text)
    next(b for b in app.button if b.label == "Submit").click().run()
    assert not app.exception


def test_the_whole_mixed_order_is_interpreted_executed_and_recorded(encounter):
    app = encounter
    before = deepcopy(app.session_state.state["observable"])
    submit(app, ORDER)

    actions = app.session_state.last_parse["actions"]
    by_type = {}
    for action in actions:
        by_type.setdefault(action["type"], []).append(action)

    # Quantity, units and the fluid's identity survive the mixed sentence.
    assert by_type["fluid"] == [{"type": "fluid", "volume_ml": 1000, "fluid_type": "normal saline"}]
    # "4l/m" is a flow rate on a named device, never a fluid volume.
    assert by_type["oxygen"] == [{"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4.0}]
    # Three separate investigations, and VBG is venous, not arterial.
    assert [a["diagnostic"] for a in by_type["diagnostic"]] == ["pocus", "vbg", "lactate"]
    assert "abg" not in [a["diagnostic"] for a in by_type["diagnostic"]]
    # Exactly one time advance, taken from the resident's own interval.
    assert by_type["reassessment"] == [{"type": "reassessment", "delay_min": 10.0}]
    assert not app.session_state.last_parse["recognized_future_actions"]

    reasoning = app.session_state.last_parse["reasoning"]
    assert reasoning["problem_representation"] == "in shock"
    assert reasoning["expected_effect"] == "improve oxygenation and perfusion"
    assert reasoning["reassessment_target"] == "hr,bp, O2"
    # A slot the app composed is labelled as such and never attributed silently.
    if reasoning.get("management_priority"):
        assert "management_priority" in reasoning.get("derived_slots", [])

    state = app.session_state.state
    assert state["sim_time"] == 10
    # Both treatments ran; neither was dropped because of the investigations.
    assert state["treatments"]["oxygen"] is True
    assert state["treatments"]["oxygen_flow_lpm"] == 4.0
    assert "nasal cannula" in str(state["treatments"]["oxygen_device"]).lower()
    # Ordered 1000 mL over 20 minutes; at the 10 minute reassessment half is in.
    assert state["family_state"]["fluid_delivered_ml"] == 500
    assert state["family_state"]["pending_fluid_ml"] == 500
    assert state["treatments"]["cumulative_crystalloid_ml"] == 500
    # All three results were released by the reassessment, none left hanging.
    assert set(state["diagnostics"]) == {"pocus", "vbg", "lactate"}
    assert not state["pending_investigations"]
    assert state["observable"] != before

    texts = [e["text"] for e in app.session_state.events if e["kind"] == "clinical_update"]
    assert texts, "the resident must be told what happened"
    # The update must not claim the full ordered volume was infused.
    assert "500 mL of 1000 mL infused" in texts[-1]

    trace = app.session_state.management_trace
    assert len(trace) == 1
    assert trace[0]["learner_input"] == ORDER
    assert trace[0]["decision_time_min"] == 0 and trace[0]["response_time_min"] == 10


def test_clarifying_one_item_executes_the_rest_of_the_original_order(encounter):
    """The reported incident: one unreadable item cost the resident every order.

    Answering the clarification then executed only the replacement study and
    advanced the clock, so the patient deteriorated untreated.
    """
    app = encounter
    submit(app, ORDER.replace("VBG", "a thromboelastogram"))
    state = app.session_state.state
    # Nothing ran and no time passed while the item is unresolved.
    assert state["sim_time"] == 0
    assert not state["treatments"].get("oxygen")
    assert not state["diagnostics"]
    # The resident is told which fragment failed, and the rest is held.
    clarifications = [e["text"] for e in app.session_state.events if e["kind"] == "clarification"]
    assert "thromboelastogram" in clarifications[-1]
    assert app.session_state.pending_action is not None

    submit(app, "ok basic labs")
    state = app.session_state.state
    # The whole original intent runs, not just the replacement study.
    assert state["sim_time"] == 10
    assert state["treatments"]["oxygen"] is True
    assert state["treatments"]["oxygen_flow_lpm"] == 4.0
    assert state["family_state"]["fluid_delivered_ml"] == 500
    assert set(state["diagnostics"]) == {"pocus", "lactate", "basic_labs"}
    assert app.session_state.pending_action is None


def test_skipping_the_unreadable_item_keeps_every_other_order(encounter):
    app = encounter
    submit(app, ORDER.replace("VBG", "a thromboelastogram"))
    submit(app, "skip that item")
    state = app.session_state.state
    assert state["sim_time"] == 10
    assert state["treatments"]["oxygen"] is True
    assert state["family_state"]["fluid_delivered_ml"] == 500
    assert set(state["diagnostics"]) == {"pocus", "lactate"}


def test_a_bare_cancel_still_drops_the_whole_held_submission(encounter):
    """"Cancel" on its own means the pending orders, not just the held item."""
    app = encounter
    submit(app, ORDER.replace("VBG", "a thromboelastogram"))
    submit(app, "cancel")
    state = app.session_state.state
    assert state["sim_time"] == 0
    assert not state["treatments"].get("oxygen")
    assert not state["diagnostics"]
    assert app.session_state.pending_action is None


def test_a_requested_reassessment_is_reported_as_one_even_when_results_arrive_first(encounter):
    # Reported encounter: POCUS alone with a 3-minute reassessment. The result
    # arrived at 00:02, yet the card said "While awaiting diagnostic results".
    app = encounter
    submit(app, "Probable sepsis. My priority is perfusion. Order POCUS. "
                "I expect to define volume status. Reassess perfusion in 3 minutes.")
    updates = [e["text"] for e in app.session_state.events if e["kind"] == "clinical_update"]
    assert updates, app.session_state.events
    assert not any("awaiting diagnostic results" in text for text in updates), updates
    assert updates[-1].startswith("After 3 minutes, "), updates
    results = [e["text"] for e in app.session_state.events if e["kind"] == "diagnostic_result"]
    assert results and all("sample obtained" not in text for text in results), results
