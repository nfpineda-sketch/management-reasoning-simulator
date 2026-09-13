"""End-to-end bedside interaction tests (no paid AI requests or image fixtures)."""
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from markdown_it import MarkdownIt
from streamlit.testing.v1 import AppTest

from curriculum import CHALLENGES


def widget(elements, label):
    return next(item for item in elements if item.label == label)


@pytest.fixture
def bedside(monkeypatch):
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30)
    app.secrets["APP_PASSWORD"] = "test-only"
    app.session_state["_shared_access_granted"] = True
    app.run()
    assert not app.exception
    selector = widget(app.selectbox, "Clinical problem")
    assert len(selector.options) == len(CHALLENGES) == 3
    assert all("PS001" not in label and "PS002" not in label for label in selector.options)
    selector.set_value("R1-03").run()
    widget(app.button, "Begin Encounter").click().run()
    assert not app.exception
    return app


def test_bedside_has_live_monitor_and_ecg_acquisition_without_code_leak(bedside):
    assert not any(button.label == "Enlarge ECG" for button in bedside.button)
    widget(bedside.button, "ECG")
    scene = next(item.value for item in bedside.markdown if 'class="clinical-scene' in item.value)
    assert "BEDSIDE MONITOR" in scene
    assert "<svg" in scene
    # The old failure was indented SVG becoming a visible Markdown code block.
    rendered = MarkdownIt("commonmark", {"html": True}).render(scene)
    assert "<pre>" not in rendered and "<code>" not in rendered
    assert "&lt;svg" not in rendered
    assert not bedside.code
    assert widget(bedside.radio, "Encounter").options == ["Talk", "Examine", "Tests", "Treat"]


def test_ecg_dialog_renders_twelve_leads_and_freezes_each_acquisition(bedside):
    widget(bedside.button, "ECG").click().run()
    assert not bedside.exception
    first = deepcopy(bedside.session_state.state["diagnostics"]["ecg"][0])
    assert first["status"] == "available"
    svg = next(item.value for item in bedside.markdown if 'aria-label="12-lead simulated ECG' in item.value)
    root = ET.fromstring(svg)
    leads = [item.attrib["data-lead"] for item in root.iter() if "data-lead" in item.attrib]
    assert set(leads) == {"I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"}
    assert len(leads) == 13  # twelve panels and the long rhythm strip
    assert "25 mm/s" in svg and "10 mm/mV" in svg
    assert not bedside.code

    # Advance the clinical state, then request another independent ECG.
    live = deepcopy(bedside.session_state.state)
    live["observable"].update(hr=75, rhythm="Sinus rhythm")
    live["sim_time"] = 5
    bedside.session_state.state = live
    bedside.run()
    widget(bedside.button, "ECG").click().run()
    assert not bedside.exception
    recordings = bedside.session_state.state["diagnostics"]["ecg"]
    assert len(recordings) == 2
    assert recordings[0] == first
    assert recordings[1]["heart_rate"] == 75
    assert recordings[1]["acquired_at_minutes"] == 5
    assert recordings[1]["recording_id"] != first["recording_id"]
    before_viewing = deepcopy(bedside.session_state.state)
    widget(bedside.selectbox, "Acquisition").set_value(0).run()
    widget(bedside.button, "View recording").click().run()
    assert not bedside.exception
    displayed = next(item.value for item in bedside.markdown if 'aria-label="12-lead simulated ECG' in item.value)
    assert displayed == svg
    assert bedside.session_state.state == before_viewing


def test_exploring_patient_preserves_state_and_management_remains_reachable(bedside):
    before = deepcopy(bedside.session_state.state)
    widget(bedside.radio, "Encounter").set_value("Talk").run()
    widget(bedside.selectbox, "Explore").set_value("Associated symptoms").run()
    widget(bedside.button, "Ask about this topic").click().run()
    assert not bedside.exception
    assert bedside.session_state.state == before
    assert bedside.session_state.events[-1]["kind"] == "patient_history"

    widget(bedside.radio, "Encounter").set_value("Examine").run()
    widget(bedside.selectbox, "Examine").set_value("General appearance").run()
    widget(bedside.button, "Examine patient").click().run()
    assert not bedside.exception
    assert bedside.session_state.state == before
    assert bedside.session_state.events[-1]["kind"] == "examination"
    assert before["observable"]["mental_status"] in bedside.session_state.events[-1]["text"]

    for mode in ("Tests", "Treat"):
        widget(bedside.radio, "Encounter").set_value(mode).run()
        assert not bedside.exception
        assert bedside.text_area
        widget(bedside.button, "Submit")
        widget(bedside.button, "ECG")
        assert any('class="clinical-scene' in item.value for item in bedside.markdown)
    assert bedside.session_state.state == before


def test_unresponsive_patient_cannot_supply_new_history(bedside):
    live = deepcopy(bedside.session_state.state)
    live['observable']['mental_status'] = 'Unresponsive'
    bedside.session_state.state = live
    widget(bedside.radio, 'Encounter').set_value('Talk').run()
    assert not bedside.exception
    assert not any(b.label in {'Ask', 'Ask about this topic'} for b in bedside.button)
    assert any('cannot provide a history' in message.value for message in bedside.info)
    assert bedside.session_state.state == live


def test_patient_answers_screenshot_question_and_targeted_followup(bedside):
    before = deepcopy(bedside.session_state.state)
    widget(bedside.radio, 'Encounter').set_value('Talk').run()
    widget(bedside.text_input, 'Ask the patient').set_value('How can I help you?').run()
    widget(bedside.button, 'Ask').click().run()
    assert not bedside.exception
    reply = bedside.session_state.events[-1]
    assert reply['kind'] == 'patient_history'
    assert 'presents with' in reply['text']
    assert 'urinate' not in reply['text'] and 'unavailable' not in reply['text']
    widget(bedside.text_input, 'Ask the patient').set_value('¿Le arde al orinar?').run()
    widget(bedside.button, 'Ask').click().run()
    assert not bedside.exception
    assert 'burned when I urinate' in bedside.session_state.events[-1]['text']
    assert bedside.session_state.state == before
