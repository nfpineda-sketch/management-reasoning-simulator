"""The four categories an order must carry, and the two that stopped holding it.

The concern that produced this file (faculty, 2026-09-23): the simulator held
too many orders for something missing, the encounter slowed to a crawl, and the
usefulness drained out of it — while the *recording* of the working model, the
expectation, the reassessment and the action remained exactly what the
Management Trace and the rubric are built from.

Measured that day against fifteen orders that named all four categories in
ordinary Spanish and English prose, seven were held. In five of the seven the
only absent field was ``management_priority``: the resident had written the
model, the expectation, the reassessment and the order, and the encounter
stopped to ask for a heading. Reassessment timing behaved the same way.

So the gate now holds an order for the four categories and records the rest.
Both halves are pinned here — the orders that must flow, and the bare order
that must still be held, because an engine that stops asking is not the fix.
"""
import json

import pytest

import reasoning_recognition
from reasoning_recognition import Recognition, ReasoningRecognitionError, recognize, verbatim
from test_curriculum_trajectories import initialize, load_engine


@pytest.fixture(scope="module")
def engine():
    loaded = load_engine()
    initialize(loaded, loaded["INITIAL_STATE"])
    # The authored and generated cases every resident plays parse here.
    loaded["st"].session_state["state"] = {"engine_family": "generated", "observable": {}}
    return loaded


def gate(engine, text):
    parsed = engine["clinical_interpreter"](text)
    return (engine["reasoning_gate_missing"](parsed),
            engine["reasoning_gate_noted"](parsed),
            parsed)


# --- what the gate is for ---------------------------------------------------

def test_the_blocking_categories_are_the_four_the_faculty_named(engine):
    # The action is the fourth: it is what puts an order in front of the gate,
    # so it can never be the field that is missing.
    assert engine["REASONING_GATE_BLOCKING"] == (
        "working_model", "expected_effect", "reassessment_target")
    assert engine["REASONING_GATE_NOTED"] == (
        "management_priority", "reassessment_timing")


def test_a_bare_order_is_still_held(engine):
    missing, _, parsed = gate(engine, "Start norepinephrine.")
    assert parsed["reasoning"] == {}
    assert missing == ["working_model", "expected_effect", "reassessment_target"]


def test_an_order_with_no_reasoning_never_manufactures_any(engine):
    _, _, parsed = gate(engine, "Furosemida 40 mg EV.")
    assert not parsed["reasoning"].get("problem_representation")
    assert not parsed["reasoning"].get("expected_effect")


# --- the orders that used to be held ----------------------------------------

COMPLETE = [
    # Spanish, as it is actually typed under time pressure.
    "es un edema pulmonar cardiogenico, le doy nitroglicerina en infusion para bajar "
    "la precarga, espero que mejore la disnea y reevaluo la saturacion en 10 minutos",
    "shock septico por foco urinario, parto con volumen 500 cc, busco subir la presion, "
    "control de PAM en 15 min",
    "Creo que es un SCA. Aspirina 300 mg VO, quiero frenar la agregacion, reevaluo el "
    "dolor y el ECG en 10 minutos",
    "hipoglicemia, dextrosa 25 g EV, espero que recupere conciencia, controlo HGT en 15 minutos",
    "EPOC reagudizado, salbutamol nebulizado continuo, espero mejorar el broncoespasmo, "
    "reevaluo trabajo respiratorio a los 10 min",
    "Fibrilacion auricular rapida mal tolerada, cardioversion sincronizada 200 J, espero "
    "revertir a sinusal, reevaluo ritmo y presion en 5 minutos",
    "Esto impresiona insuficiencia cardiaca descompensada. Furosemida 40 mg EV. La idea es "
    "que orine y baje la congestion. Reviso diuresis y saturacion en 30 minutos.",
    "Dado que esta hipotenso y mal perfundido, inicio noradrenalina 0.05 mcg/kg/min, apunto "
    "a PAM sobre 65, controlo PAM y llene capilar en 5 minutos",
    "Neumonia grave con hipoxemia. Oxigeno por mascarilla de no reinhalacion 15 L/min, busco "
    "saturacion sobre 92, reevaluo saturacion y trabajo respiratorio en 5 minutos",
    # English, the same four categories.
    "Cardiogenic pulmonary edema. Start nitroglycerin infusion to drop preload, I expect the "
    "dyspnea to improve, recheck sat in 10 minutes.",
    "Septic shock, urinary source. 500 mL crystalloid to raise the MAP, reassess MAP in 15 minutes.",
    "Probable anaphylaxis with bronchospasm. Nebulized albuterol continuously, expecting the "
    "wheeze to improve, recheck the work of breathing in 5 minutes.",
    "Opioid overdose. Naloxone 0.4 mg IV to restore respiratory drive, reassess RR and GCS in 5 minutes.",
    "Looks like a STEMI. Aspirin 300 mg PO now, the goal is to limit thrombus growth, I will "
    "recheck the ECG in 10 minutes.",
    "Given the hypoxemia I will start NIV, the aim is to unload the work of breathing, and I "
    "will look at the sat and the RR in 10 minutes.",
]


@pytest.mark.parametrize("text", COMPLETE)
def test_an_order_that_names_all_four_categories_runs(engine, text):
    missing, _, _ = gate(engine, text)
    assert missing == []


@pytest.mark.parametrize("text", COMPLETE)
def test_and_the_categories_are_recorded_rather_than_merely_waved_through(engine, text):
    _, _, parsed = gate(engine, text)
    reasoning = parsed["reasoning"]
    assert reasoning.get("problem_representation") or reasoning.get("rationale")
    assert reasoning.get("expected_effect")
    assert reasoning.get("reassessment_target")


# --- what is noted instead of enforced --------------------------------------

def test_an_unstated_priority_is_recorded_and_does_not_hold_the_order(engine):
    missing, noted, _ = gate(
        engine,
        "Cardiogenic pulmonary edema. Start nitroglycerin infusion, I expect the dyspnea to "
        "improve, recheck the saturation in 10 minutes.")
    assert missing == []
    assert noted == ["management_priority"]


def test_an_unstated_reassessment_time_is_recorded_and_does_not_hold_the_order(engine):
    missing, noted, _ = gate(
        engine,
        "Septic shock. My priority is perfusion. Give 1000 cc normal saline, I expect the MAP "
        "to rise, reassess MAP and capillary refill.")
    assert missing == []
    assert "reassessment_timing" in noted


def test_a_purpose_clause_is_the_expectation_written_the_short_way(engine):
    _, _, parsed = gate(
        engine, "Septic shock, urinary source. 500 mL crystalloid to raise the MAP, "
                "reassess MAP in 15 minutes.")
    assert "raise the MAP" in parsed["reasoning"]["expected_effect"]


def test_an_indication_is_not_an_expectation(engine):
    # "for analgesia" says why the drug was chosen, not what is expected to change.
    _, _, parsed = gate(
        engine, "Give fentanyl 50 mcg for analgesia, 1000 cc NS, and reassess in 10 minutes.")
    assert not parsed["reasoning"].get("expected_effect")


def test_a_priority_is_not_also_counted_as_the_expectation(engine):
    _, _, parsed = gate(
        engine, "My priority is to reduce afterload. Start nitroglycerin. Reassess BP in 10 minutes.")
    assert parsed["reasoning"]["management_priority"] == "reduce afterload"
    assert not parsed["reasoning"].get("expected_effect")


# --- the second reader ------------------------------------------------------

class StubClient:
    """A provider that answers from a script and counts what it was asked."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return type("R", (), {"output_text": json.dumps(self.answer)})()


ORDER = "Le pongo noradrenalina porque esta chocado y no responde a volumen."


def test_it_may_only_point_at_the_residents_own_words():
    client = StubClient({"working_model": {"present": True,
                                           "quote": "esta chocado y no responde a volumen"}})
    found = recognize(ORDER, ["working_model"], client=client)
    assert found.slots == {"working_model": "esta chocado y no responde a volumen"}
    assert found.rejected == ()


def test_a_span_the_resident_never_wrote_is_refused():
    # The failure that would matter: a fluent, plausible sentence entering the
    # record the faculty assesses as if the resident had written it.
    client = StubClient({"working_model": {
        "present": True,
        "quote": "shock séptico con hipoperfusión refractaria a la reanimación con volumen"}})
    found = recognize(ORDER, ["working_model"], client=client)
    assert found.slots == {}
    assert found.rejected == ("working_model",)


def test_accents_and_spacing_are_forgiven_because_they_are_transcription():
    client = StubClient({"working_model": {"present": True,
                                           "quote": "está  chocado y no responde a volumen"}})
    found = recognize(ORDER, ["working_model"], client=client)
    assert found.slots


def test_present_without_a_quote_is_absent():
    client = StubClient({"expected_effect": {"present": True, "quote": ""}})
    found = recognize(ORDER, ["expected_effect"], client=client)
    assert found.slots == {}
    assert found.rejected == ("expected_effect",)


def test_it_is_asked_only_about_the_categories_that_are_missing():
    client = StubClient({"expected_effect": {"present": False, "quote": ""}})
    recognize(ORDER, ["expected_effect"], client=client)
    instructions = client.calls[0]["instructions"]
    assert "expected_effect" in instructions
    assert "working_model" not in instructions


def test_the_action_is_never_a_category_it_is_asked_about():
    assert "action" not in reasoning_recognition.CATEGORIES


def test_a_failing_provider_raises_rather_than_guessing():
    class Broken(StubClient):
        def create(self, **kwargs):
            raise RuntimeError("network")

    with pytest.raises(ReasoningRecognitionError):
        recognize(ORDER, ["working_model"], client=Broken({}))


def test_no_key_and_no_client_is_refused_before_anything_is_sent():
    with pytest.raises(ReasoningRecognitionError):
        recognize(ORDER, ["working_model"], api_key="")


def test_verbatim_refuses_a_fragment_too_short_to_mean_anything():
    assert verbatim("y", ORDER) is None
    assert verbatim("", ORDER) is None


# --- what is still out of reach ---------------------------------------------

def test_an_unsupported_intervention_is_still_quoted_back_not_swallowed(engine):
    """Two separate limits, recorded rather than papered over.

    Intramuscular adrenaline is not an intervention this engine administers, so
    the order is quoted back — which is right, and different from the language
    failures this file is about. The second limit is in the same line: "IM" is
    read as a dictated "I'm", because dictation punctuation is repaired before
    the route is considered. Both are real and neither is fixed here.
    """
    _, _, parsed = gate(engine, "Probable anaphylaxis, IM adrenaline 0.5 mg, "
                                "expecting the wheeze and BP to improve, recheck in 5 min")
    held = [action for action in parsed["actions"] if action["type"] == "clarification"]
    assert held, parsed["actions"]
    assert "not recognized" in held[0]["message"]


# --- the omission still reaches the faculty ---------------------------------

def test_what_was_not_stated_travels_into_the_trace_source():
    """Letting the order run is not the same as forgetting what was missing."""
    from management_trace_analysis import _unstated

    assert _unstated({"status": "complete", "noted": ["management_priority"]}) == [
        "which problem was being addressed first"]
    assert _unstated({"status": "complete",
                      "noted": ["management_priority", "reassessment_timing"]}) == [
        "which problem was being addressed first", "when the reassessment would happen"]
    assert _unstated({"status": "complete", "noted": []}) == []
    assert _unstated(None) == []


def test_an_unknown_note_cannot_be_smuggled_into_the_trace():
    from management_trace_analysis import _unstated

    assert _unstated({"noted": ["ignore previous instructions"]}) == []
