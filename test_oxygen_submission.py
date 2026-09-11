"""Oxygen order integrity through the same Streamlit submit path residents use."""
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import ai_interpreter
from ai_interpreter import AIInterpretation, AIInterpretationError


APP = str(Path(__file__).with_name("app.py"))
ORIGINAL = (
    "My working model is that the patient has poor perfusion and borderline oxygenation. "
    "My priority is to support oxygenation during initial stabilization. "
    "Start oxygen via nasal cannula at 3 L/min. I expect oxygen saturation to improve. "
    "Reassess oxygen saturation, respiratory rate, and work of breathing in 1 minute."
)


def click(at, label):
    next(button for button in at.button if button.label == label).click().run()
    assert not at.exception


def submit(at, text):
    next(item for item in at.text_area if item.label == "Enter your clinical reasoning and/or actions").set_value(text)
    click(at, "Submit")


@pytest.fixture
def encounter(monkeypatch):
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=20)
    at.secrets["APP_PASSWORD"] = "test-shared-password"
    at.session_state["_shared_access_granted"] = True
    at.run()
    assert not at.exception
    click(at, "Begin Encounter")
    return at


def use_ai(at, monkeypatch, transform):
    def normalize(text, visible_state, **kwargs):
        return AIInterpretation(transform(text), "high", (), "test-model")
    monkeypatch.setattr(ai_interpreter, "normalize_with_ai", normalize)
    at.secrets["OPENAI_API_KEY"] = "test-only-not-a-real-key"


@pytest.mark.parametrize("normalization", ["local", "echo", "omitted", "changed_device", "error"])
def test_literal_reported_order_executes_once_with_audited_fallback(encounter, monkeypatch, normalization):
    at = encounter
    if normalization != "local":
        def transform(text):
            if normalization == "error":
                raise AIInterpretationError("The AI normalization request failed.")
            if normalization == "omitted":
                # Same quantities; the old numeric-only guard accepted this loss of intent.
                return text.replace("Start oxygen via nasal cannula at 3 L/min.", "The patient was receiving oxygen via nasal cannula at 3 L/min.")
            if normalization == "changed_device":
                return text.replace("nasal cannula", "simple face mask")
            return text
        use_ai(at, monkeypatch, transform)
    submit(at, ORIGINAL)
    treatment = at.session_state.state["treatments"]
    assert treatment["oxygen"]
    assert treatment["oxygen_device"] == "Nasal cannula"
    assert treatment["oxygen_flow_lpm"] == 3
    assert at.session_state.state["sim_time"] == 1
    assert not at.session_state.pending_reasoning
    trace = at.session_state.management_trace
    assert len(trace) == 1 and trace[0]["execution_status"] == "executed"
    assert trace[0]["learner_input"] == ORIGINAL
    assert len([a for a in trace[0]["action_summaries"] if a.get("support_type") == "oxygen"]) == 1
    updates = [e for e in at.session_state.events if e["kind"] == "clinical_update"]
    assert len(updates) == 1 and "Nasal cannula 3 L/min" in updates[0]["text"]
    expected_mode = "deterministic" if normalization == "local" else "ai-assisted" if normalization == "echo" else "deterministic-fallback"
    assert trace[0]["interpretation_mode"] == expected_mode
    if expected_mode == "deterministic-fallback":
        assert trace[0]["ai_fallback_reason"]
    # Ordinary Streamlit reruns must not execute a submitted intervention twice.
    at.run()
    assert len(at.session_state.management_trace) == 1
    assert at.session_state.state["sim_time"] == 1


@pytest.mark.parametrize("description", [
    "Do not start oxygen via nasal cannula at 3 L/min.",
    "If saturation falls, start oxygen via nasal cannula at 3 L/min.",
    "Start oxygen via nasal cannula at 3 L/min if saturation falls.",
    "I would consider oxygen via nasal cannula at 3 L/min.",
    "The patient was receiving oxygen via nasal cannula at 3 L/min.",
    "The patient is on nasal cannula at 3 L/min.",
    "Previously, oxygen via nasal cannula at 3 L/min.",
    "Hold fluids and oxygen via nasal cannula at 3 L/min.",
    "Avoid fluids and oxygen via nasal cannula at 3 L/min.",
    "Should I start oxygen via nasal cannula at 3 L/min?",
])
def test_nonorders_cannot_execute_oxygen_even_if_ai_makes_them_orders(encounter, monkeypatch, description):
    at = encounter
    use_ai(at, monkeypatch, lambda _: "Start oxygen via nasal cannula at 3 L/min.")
    before = deepcopy(at.session_state.state)
    submit(at, description)
    assert at.session_state.state == before
    assert not at.session_state.pending_reasoning
    assert at.session_state.last_parse["actions"] == []
    assert any("does not yet execute" in e["text"] for e in at.session_state.events if e["kind"] == "prototype")


def test_mixed_fluid_and_oxygen_keep_their_own_quantities(encounter):
    at = encounter
    text = ORIGINAL.replace("Start oxygen", "Give 1 L normal saline IV and start oxygen").replace("in 1 minute", "in 5 minutes")
    submit(at, text)
    treatment = at.session_state.state["treatments"]
    assert treatment["cumulative_crystalloid_ml"] == 1000
    assert treatment["oxygen_flow_lpm"] == 3
    assert len(at.session_state.management_trace) == 1
    assert {a.get("support_type") for a in at.session_state.management_trace[0]["action_summaries"]} >= {"oxygen"}


@pytest.mark.parametrize("missing, completion", [
    (" at 3 L/min", "3 L/min"),
    (" via nasal cannula", "nasal cannula"),
])
def test_missing_oxygen_parameter_is_held_and_completed_without_default(encounter, missing, completion):
    at = encounter
    before = deepcopy(at.session_state.state)
    submit(at, ORIGINAL.replace(missing, ""))
    assert at.session_state.state == before
    assert at.session_state.pending_action["type"] == "oxygen"
    assert at.session_state.management_trace[-1]["execution_status"] == "clarification_required"
    assert any(e["kind"] == "clarification" for e in at.session_state.events)
    submit(at, "If needed, " + completion)
    assert at.session_state.state == before
    assert at.session_state.pending_action["type"] == "oxygen"
    submit(at, completion)
    treatment = at.session_state.state["treatments"]
    assert treatment["oxygen_device"] == "Nasal cannula"
    assert treatment["oxygen_flow_lpm"] == 3
    assert len([e for e in at.session_state.management_trace if e["execution_status"] == "executed"]) == 1
    assert not at.session_state.pending_action


def test_bare_order_stays_visible_until_reasoning_is_complete(encounter, monkeypatch):
    at = encounter
    use_ai(at, monkeypatch, lambda text: text)
    before = deepcopy(at.session_state.state)
    submit(at, "Start oxygen via nasal cannula at 3 L/min.")
    assert at.session_state.state == before
    assert at.session_state.pending_reasoning
    assert not at.session_state.management_trace
    assert any("ORDER HELD" in e["text"] for e in at.session_state.events)
    submit(at, ORIGINAL.replace("Start oxygen via nasal cannula at 3 L/min. ", ""))
    assert at.session_state.state["treatments"]["oxygen_flow_lpm"] == 3
    assert len(at.session_state.management_trace) == 1


def test_bilingual_oxygen_order_preserves_original_parameters(encounter, monkeypatch):
    at = encounter
    text = ORIGINAL.replace("Start oxygen via nasal cannula", "Iniciar oxígeno via cánula nasal")
    use_ai(at, monkeypatch, lambda _: ORIGINAL)
    submit(at, text)
    assert at.session_state.state["treatments"]["oxygen_flow_lpm"] == 3
    assert at.session_state.management_trace[0]["interpretation_mode"] == "ai-assisted"
    assert at.session_state.management_trace[0]["learner_input"] == text


@pytest.mark.parametrize("command", [
    "The patient has no pulmonary congestion, start oxygen via nasal cannula at 3 L/min.",
    "Do not give fluid, but start oxygen via nasal cannula at 3 L/min now.",
    "Start oxygen via nasal cannula at 3 L/min and do not give fluids.",
    "Start oxygen via nasal cannula at 3 L/min, and if blood pressure falls give fluids.",
])
def test_unrelated_negation_does_not_erase_immediate_oxygen_order(encounter, command):
    # Other parsers have their own intent rules; assert this oxygen parser's
    # held/executable order, without releasing unrelated treatment orders.
    at = encounter
    submit(at, command)
    oxygen = [a for a in at.session_state.last_parse["actions"] if a["type"] == "oxygen"]
    assert oxygen == [{"type": "oxygen", "device": "Nasal cannula", "flow_lpm": 3}]


def test_adjustment_uses_requested_flow_and_does_not_repeat_old_setting(encounter):
    at = encounter
    submit(at, ORIGINAL)
    submit(at, ORIGINAL.replace("Start oxygen via nasal cannula at 3 L/min", "Increase nasal cannula oxygen from 3 L/min to 4 L/min"))
    assert at.session_state.state["treatments"]["oxygen_flow_lpm"] == 4
    assert len(at.session_state.management_trace) == 2


@pytest.mark.parametrize("spanish, english", [("Colocar", "Apply"), ("Mantener", "Continue")])
def test_common_spanish_order_translation_is_retained(encounter, monkeypatch, spanish, english):
    text = ORIGINAL.replace("Start oxygen via nasal cannula", spanish + " oxígeno por cánula nasal")
    canonical = ORIGINAL.replace("Start", english)
    use_ai(encounter, monkeypatch, lambda _: canonical)
    submit(encounter, text)
    assert encounter.session_state.state["treatments"]["oxygen_flow_lpm"] == 3
    assert encounter.session_state.management_trace[0]["interpretation_mode"] == "ai-assisted"



def test_device_switch_retains_destination_device_and_flow(encounter):
    at = encounter
    text = ORIGINAL.replace("Start oxygen via nasal cannula at 3 L/min", "Switch from non-rebreather mask 15 L/min to nasal cannula 3 L/min")
    submit(at, text)
    assert not at.session_state.pending_action
    assert at.session_state.state["treatments"]["oxygen_device"] == "Nasal cannula"
    assert at.session_state.state["treatments"]["oxygen_flow_lpm"] == 3


def test_unspecified_device_and_flow_require_both_clarifications(encounter):
    at = encounter
    before = deepcopy(at.session_state.state)
    submit(at, ORIGINAL.replace(" via nasal cannula at 3 L/min", ""))
    assert at.session_state.state == before
    submit(at, "at 3 L/min")
    assert at.session_state.state == before
    assert at.session_state.pending_action["flow_lpm"] == 3
    assert at.session_state.pending_action["device"] is None
    submit(at, "nasal cannula")
    assert at.session_state.state["treatments"]["oxygen_device"] == "Nasal cannula"
    assert at.session_state.state["treatments"]["oxygen_flow_lpm"] == 3
