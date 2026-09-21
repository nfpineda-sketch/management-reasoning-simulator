"""How oxygen is ordered at the bedside, and what a held order tells the resident.

Two faculty decisions of 2026-09-20, found by playing the pneumonia case: a bare
"mask" (or "mascarilla") is a real oxygen order and must not stall the turn, and
when one ambiguous item does hold a turn, the resident has to be told what else
was understood. The first version of that clarification was a single line, so an
antibiotic and four investigations disappeared behind a quibble about a device.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))
SEPSIS_ORDER = (
    "Pneumonia with septic hypoperfusion. Priority: treat the infection and support "
    "oxygenation. Start high-flow nasal oxygen, give ceftriaxone 2 g IV, and order blood "
    "cultures, lactate, basic labs and a chest X-ray. I expect the lactate to fall. "
    "Reassess in 15 minutes blood pressure, saturation and perfusion."
)


def oxygen(text):
    actions = parse_family_actions(text)["actions"]
    return next((a for a in actions if a.get("type") == "oxygen"), None), [a.get("type") for a in actions]


@pytest.mark.parametrize("text, device, flow", [
    ("Give oxygen by mask at 10 L/min.", "simple mask", 10.0),
    ("Give oxygen by face mask at 10 L/min.", "simple mask", 10.0),
    ("Give oxygen by simple mask at 8 L/min.", "simple mask", 8.0),
    # Spanish reaches the same device without having to say "simple".
    ("Dale oxigeno por mascarilla a 10 L/min.", "simple mask", 10.0),
    # The named devices still win over the bare word they contain.
    ("Give oxygen by non-rebreather mask at 15 L/min.", "non-rebreather mask", 15.0),
    ("Oxigeno por mascarilla con reservorio a 15 L/min.", "non-rebreather mask", 15.0),
    ("Start oxygen by nasal cannula at 4 L/min.", "nasal cannula", 4.0),
    ("Switch from nasal cannula to a mask at 10 L/min.", "simple mask", 10.0),
])
def test_a_bare_mask_is_a_supported_oxygen_device(text, device, flow):
    action, types = oxygen(text)
    assert "clarification" not in types, types
    assert action["device"] == device and action["flow_lpm"] == flow


@pytest.mark.parametrize("text, expected", [
    # A mask that is not an oxygen interface is still not an oxygen order.
    ("Ventilate with a bag-mask.", "bag_mask"),
    ("Start CPAP 8 cm H2O by mask.", "niv"),
])
def test_other_masks_are_not_oxygen_orders(text, expected):
    action, types = oxygen(text)
    assert action is None and types == [expected]


def test_the_clarification_names_the_devices_that_exist():
    # Without a device there is still nothing to guess at, but the menu is named.
    for text in ("Give oxygen 10 L/min.", "Start high-flow nasal oxygen."):
        actions = parse_family_actions(text)["actions"]
        message = next(a["message"] for a in actions if a.get("type") == "clarification")
        assert "nasal cannula 4 L/min" in message
        assert "simple mask 8 L/min" in message
        assert "non-rebreather mask 15 L/min" in message


@pytest.fixture
def encounter(monkeypatch):
    from test_curriculum_app import authored_replay_fixture
    authored_replay_fixture(monkeypatch)
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["APP_PASSWORD"] = "test-shared-password"
    at.session_state["_shared_access_granted"] = True
    at.run()
    assert not at.exception
    next(b for b in at.button if b.label == "Begin Encounter").click().run()
    assert not at.exception
    return at


def test_a_held_turn_names_the_orders_it_is_holding(encounter):
    at = encounter
    next(item for item in at.text_area if item.label == "Enter your clinical reasoning and/or actions").set_value(SEPSIS_ORDER)
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception
    held = [e["text"] for e in at.session_state.events if e["kind"] == "clarification"]
    assert held, "the held turn must be reported to the resident"
    text = held[-1]
    assert "ORDER HELD — CLARIFICATION REQUIRED" in text
    assert "Nothing in this order was executed and the patient state has not changed." in text
    # Everything the resident also asked for, by name.
    for item in ("ceftriaxone 2000 mg IV", "Blood cultures", "Lactate", "Laboratory results", "Chest X-ray"):
        assert item in text, (item, text)
    # And the device menu, so the turn can be completed in one reply.
    assert "non-rebreather mask 15 L/min" in text
    # Nothing ran: no treatment, no investigation, no time.
    assert at.session_state.state["sim_time"] == 0
    assert not at.session_state.state.get("diagnostics")
