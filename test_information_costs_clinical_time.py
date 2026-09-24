"""Obtaining information is a clinical activity, and the patient lives through it.

Faculty specification of 2026-09-23. Until that day a resident could ask the
patient anything, examine them anywhere and read every result without a single
simulated minute passing: the clock moved only for treatments, reassessments and
studies. A patient who was unstable and untreated stayed exactly as unstable for
as long as the resident wanted to investigate, which taught the opposite of what
an emergency department teaches.

Two things are pinned here and they pull against each other, which is why both
are tests rather than one being an assumption:

* **Information costs time**, differentiated by activity, and the illness, the
  treatments already given and the results still pending all run through those
  minutes on the same temporal engine as any order.
* **Nothing is charged for friction**, and no patient is made worse *because* a
  question was asked. Reaching the same clinical minute with the same
  interventions produces the same patient, whether it took one message or six.
"""
from copy import deepcopy

import pytest

import clinical_time
import family_engine
from test_cognitive_encounters import encounter as build_encounter
from test_curriculum_trajectories import execute_turn, initialize, load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def play(engine, family, case_id, orders):
    generated = build_encounter(engine, family, case_id)
    session = initialize(engine, deepcopy(generated["state"]))
    results = []
    for text in orders:
        _, result, _, _ = execute_turn(engine, text)
        results.append(result)
    return session, results


def minutes(engine, family, case_id, text):
    _, results = play(engine, family, case_id, [text])
    return results[0].get("elapsed_min", 0)


REASONED = (" Creo que es una neumonia grave. Espero que mejore la perfusion. "
            "Reevaluo presion y saturacion en 10 minutos.")


# --- every information activity costs something, and not the same thing -----

@pytest.mark.parametrize("text, expected", [
    ("Examino la respiracion.", 2),
    ("Examino la respiracion y el abdomen.", 3),
    ("Examino la respiracion, el abdomen, el corazon y el estado neurologico.", 5),
    ("Pido un lactato.", 1),
    ("Pido un panel de laboratorio.", 1),
    ("Pido una radiografia de torax.", 1),
    ("Pido un POCUS.", 2),
    ("Pido un ECG.", 1),
    ("Revisa el lactato.", 1),
])
def test_an_information_activity_costs_its_own_minutes(engine, text, expected):
    assert minutes(engine, "pneumonia", "pneumonia_46f", text) == expected


def test_no_information_activity_is_free(engine):
    for text in ("Examino el abdomen.", "Pido un lactato.", "Revisa el lactato.",
                 "Pido un POCUS."):
        assert minutes(engine, "pneumonia", "pneumonia_46f", text) > 0, text


def test_an_examination_of_many_regions_does_not_grow_without_limit():
    assert clinical_time.examination_minutes(["a"] * 20) == clinical_time.EXAMINATION_CEILING_MINUTES


# --- the two clocks: the resident's own, and the wait for a result ----------

def test_sending_a_study_does_not_freeze_the_resident(engine):
    """Before 2026-09-23 ordering bloods cost ten minutes of dead time."""
    assert minutes(engine, "pneumonia", "pneumonia_46f", "Pido un panel de laboratorio.") == 1
    assert clinical_time.study_result_minutes("basic_labs", 10) == 10


def test_a_bedside_study_is_back_when_the_resident_stops_looking(engine):
    assert clinical_time.study_active_minutes("pocus", 2) == 2
    assert clinical_time.study_result_minutes("pocus", 2) == 2


def test_a_requested_result_waits_for_its_own_minute_and_then_arrives(engine):
    session, results = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un panel de laboratorio.",
        "Doy ceftriaxona 2 g EV." + REASONED,
        "Reevalua saturacion y presion en 5 minutos."])
    assert [p["diagnostic"] for p in family_engine.pending_results(session["state"])] == []
    delivered = [s.get("diagnostic_type") for result in results
                 for s in result["action_summaries"] if s.get("type") == "diagnostic"]
    assert delivered == ["basic_labs"]
    assert session["state"]["diagnostics"]["basic_labs"]["time_min"] == 10


def test_what_is_still_out_is_visible_while_it_is_out(engine):
    session, _ = play(engine, "pneumonia", "pneumonia_46f", ["Pido un panel de laboratorio."])
    assert family_engine.pending_results(session["state"]) == [
        {"diagnostic": "basic_labs", "available_at_min": 10}]


def test_a_result_is_never_published_before_it_is_available(engine):
    session, results = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido una radiografia de torax.", "Examino el abdomen."])
    assert session["state"]["sim_time"] == 3
    assert "chest_xray" not in session["state"].get("diagnostics", {})


def test_several_studies_are_processed_together_and_not_one_after_another(engine):
    together = minutes(engine, "pneumonia", "pneumonia_46f",
                       "Pido un lactato, gases venosos, un panel de laboratorio y una radiografia de torax.")
    assert together == 1, "four requests are still one act of requesting"


# --- reading a result is not repeating the study ----------------------------

def test_reading_a_result_does_not_repeat_the_study(engine):
    session, _ = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un lactato.", "Reevalua saturacion en 8 minutos.",
        "Revisa el lactato.", "Revisa el lactato."])
    ran = [row for row in session["state"]["diagnostic_history"]
           if row["diagnostic_type"] == "lactate"]
    assert len(ran) == 1


def test_reading_a_result_that_is_not_back_says_when_it_will_be(engine):
    _, results = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un panel de laboratorio.", "Revisa el panel de laboratorio."])
    label = results[-1]["action_summaries"][0]["label"]
    assert "not back yet" in label and "10 min" in label


def test_reading_a_result_nobody_asked_for_says_so(engine):
    _, results = play(engine, "pneumonia", "pneumonia_46f", ["Revisa el lactato."])
    assert "has not been requested" in results[0]["action_summaries"][0]["label"]


# --- the patient lives through the minutes ----------------------------------

def test_an_unstable_untreated_patient_deteriorates_while_information_is_gathered(engine):
    session, _ = play(engine, "anaphylaxis", "anaphylaxis_29f", [
        "Examino la respiracion, el abdomen y el estado general.",
        "Pido un panel de laboratorio y gases venosos.",
        "Examino el corazon.",
        "Reevalua presion y saturacion en 5 minutos."])
    o = session["state"]["observable"]
    assert session["state"]["sim_time"] == 12
    assert o["sbp"] < 75, "the reaction did not wait to be investigated"


def test_a_treated_patient_keeps_improving_while_information_is_gathered(engine):
    reason = (" Creo que es una anafilaxia. Espero que suba la presion. "
              "Reevaluo presion y saturacion en 5 minutos.")
    session, _ = play(engine, "anaphylaxis", "anaphylaxis_29f", [
        "Doy adrenalina 0.5 mg IM en el muslo." + reason,
        "Examino la respiracion, el abdomen y el estado general.",
        "Pido un panel de laboratorio y gases venosos.",
        "Examino el corazon.",
        "Reevalua presion y saturacion en 5 minutos."])
    o = session["state"]["observable"]
    assert o["sbp"] > 95 and o["mental_status"] == "Alert"


def test_a_stable_patient_is_not_made_worse_by_being_investigated(engine):
    session, _ = play(engine, "renal_colic", "renal_colic_34m", [
        "Examino el abdomen y el estado general.",
        "Pido un examen de orina y una ecografia renal.",
        "Reevalua signos vitales en 20 minutos."])
    o = session["state"]["observable"]
    assert session["state"]["sim_time"] == 24
    assert (o["sbp"], o["hr"], o["spo2"]) == (142, 94, 98)


def test_a_long_interval_surfaces_the_event_it_crosses(engine):
    generated = build_encounter(engine, "anaphylaxis", "anaphylaxis_29f")
    session = initialize(engine, deepcopy(generated["state"]))
    labels = []
    for text in ("Reevalua presion y saturacion en 15 minutos.",
                 "Reevalua presion y saturacion en 15 minutos."):
        _, result, _, _ = execute_turn(engine, text)
        labels.extend(str(s.get("label") or "") for s in result["action_summaries"])
    assert any("arrest" in text.lower() for text in labels), labels


# --- the same minute is the same patient ------------------------------------

def test_the_number_of_messages_does_not_decide_the_deterioration(engine):
    """Reaching the same clock with the same interventions is the same patient."""
    def at_twelve(orders):
        session, _ = play(engine, "anaphylaxis", "anaphylaxis_29f", orders)
        assert session["state"]["sim_time"] == 12
        o = session["state"]["observable"]
        return o["sbp"], o["dbp"], o["hr"], o["spo2"]

    one_message = at_twelve(["Reevalua presion y saturacion en 12 minutos."])
    six_examinations = at_twelve([
        "Examino la respiracion.", "Examino el abdomen.", "Examino el corazon.",
        "Examino el estado general.", "Examino la respiracion.", "Examino el abdomen."])
    three_and_a_wait = at_twelve([
        "Examino la respiracion.", "Examino el abdomen.", "Examino el corazon.",
        "Reevalua presion en 6 minutos."])
    assert one_message == six_examinations == three_and_a_wait


# --- information never asks for the four categories -------------------------

@pytest.mark.parametrize("text", [
    "Examino la respiracion.",
    "Examino el abdomen y el corazon.",
    "Pido un lactato.",
    "Pido un lactato, un POCUS y una radiografia de torax.",
    "Revisa el lactato.",
    "Pido un ECG.",
])
def test_obtaining_information_never_opens_the_follow_up(engine, text):
    parsed = engine["clinical_interpreter"](text)
    assert engine["reasoning_gate_missing"](parsed) == []
    assert not parsed.get("clarification")


def test_one_entry_may_mix_an_examination_a_study_and_a_treatment(engine):
    """Each component is processed; none of them is lost or refuses the rest."""
    text = "Examino la respiracion, doy ceftriaxona 2 g EV y pido un lactato." + REASONED
    parsed = engine["clinical_interpreter"](text)
    assert [a["type"] for a in parsed["actions"]] == [
        "examination", "antibiotics", "diagnostic", "reassessment"]
    session, results = play(engine, "pneumonia", "pneumonia_46f", [text])
    assert not results[0].get("clarification")
    assert len(session["state"]["treatments"]["administered_medications"]) == 1
    # The examination happened, the drug was given, and the lactate is out: the
    # resident is not waiting for it before doing the rest.
    assert "examination" in {s.get("type") for s in results[0]["action_summaries"]}
    assert session["state"]["diagnostics"].get("lactate")


# --- friction is not clinical time ------------------------------------------

def test_a_refused_order_costs_no_clinical_time(engine):
    generated = build_encounter(engine, "pneumonia", "pneumonia_46f")
    session = initialize(engine, deepcopy(generated["state"]))
    result = engine["execute_bundle"](
        engine["clinical_interpreter"]("Doy vancomicina 1 g intraperitoneal."))
    assert result.get("elapsed_min") == 0
    assert session["state"]["sim_time"] == 0


def test_completing_the_follow_up_costs_no_clinical_time_and_executes_once(engine):
    generated = build_encounter(engine, "pneumonia", "pneumonia_46f")
    session = initialize(engine, deepcopy(generated["state"]))
    parsed = engine["clinical_interpreter"]("Doy ceftriaxona 2 g EV.")
    engine["hold_pending_reasoning"](parsed)
    assert session["state"]["sim_time"] == 0
    resolved = engine["resolve_pending_reasoning"](
        "Creo que es una neumonia grave. Espero que mejore la perfusion. "
        "Reevaluo presion en 10 minutos.")
    assert session["state"]["sim_time"] == 0, "the form is not a clinical activity"
    engine["execute_bundle"](resolved["parsed"])
    assert len(session["state"]["treatments"]["administered_medications"]) == 1


# --- and the record says what the interval was spent on ---------------------

def test_the_trace_source_accepts_an_information_activity():
    from management_trace_analysis import _STATUSES, _pending
    assert "information" in _STATUSES
    assert _pending([{"diagnostic": "basic_labs", "available_at_min": 10}]) == [
        {"diagnostic": "basic_labs", "available_at_min": 10}]
    # Anything that is not a study with a minute is dropped rather than shown.
    assert _pending([{"diagnostic": 5, "available_at_min": 10}]) == []
    assert _pending("not a list") == []


def test_the_time_table_says_it_is_an_assumption():
    source = open(clinical_time.__file__, encoding="utf-8").read()
    assert "pending clinical calibration" in source
    assert "Interface friction is not clinical time" in source or (
        "friction is not clinical time" in source)


# --- the screens that obtain information, driven as a resident drives them --

APP = str(__import__("pathlib").Path(__file__).with_name("app.py"))


@pytest.fixture
def bedside(monkeypatch):
    """A real encounter of a family case, opened in the app itself."""
    from streamlit.testing.v1 import AppTest
    from test_curriculum_app import authored_replay_fixture

    authored_replay_fixture(monkeypatch)
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["APP_PASSWORD"] = "test-shared-password"
    at.session_state["_shared_access_granted"] = True
    at.run()
    assert not at.exception
    for _ in range(40):
        next(b for b in at.button if b.label == "Begin Encounter").click().run()
        assert not at.exception
        if at.session_state.state.get("engine_family"):
            return at
        next(b for b in at.button if b.label == "Reset scenario").click().run()
    pytest.skip("no family encounter was drawn")


def widget(elements, label):
    return next(item for item in elements if item.label == label)


def test_asking_the_patient_costs_clinical_time(bedside):
    widget(bedside.radio, "Encounter").set_value("Talk").run()
    before = int(bedside.session_state.state["sim_time"])
    widget(bedside.selectbox, "Explore").set_value(
        bedside.selectbox[[i.label for i in bedside.selectbox].index("Explore")].options[0]).run()
    widget(bedside.button, "Ask about this topic").click().run()
    assert not bedside.exception
    assert int(bedside.session_state.state["sim_time"]) == before + clinical_time.ACTIVE_MINUTES[
        "history_question"]
    assert bedside.session_state.events[-1]["kind"] == "patient_history"


def test_examining_the_patient_costs_clinical_time(bedside):
    widget(bedside.radio, "Encounter").set_value("Examine").run()
    before = int(bedside.session_state.state["sim_time"])
    widget(bedside.selectbox, "Examine").set_value("General appearance").run()
    widget(bedside.button, "Examine patient").click().run()
    assert not bedside.exception
    assert int(bedside.session_state.state["sim_time"]) == before + clinical_time.ACTIVE_MINUTES[
        "examination_region"]


def test_switching_screens_costs_nothing(bedside):
    """Interface friction is not clinical time, and re-rendering is friction."""
    before = int(bedside.session_state.state["sim_time"])
    for mode in ("Talk", "Examine", "Tests", "Treat", "Talk"):
        widget(bedside.radio, "Encounter").set_value(mode).run()
        assert not bedside.exception
    bedside.run()
    bedside.run()
    assert int(bedside.session_state.state["sim_time"]) == before


def test_the_interval_spent_obtaining_information_is_in_the_trace(bedside):
    widget(bedside.radio, "Encounter").set_value("Examine").run()
    widget(bedside.selectbox, "Examine").set_value("General appearance").run()
    widget(bedside.button, "Examine patient").click().run()
    entry = bedside.session_state.management_trace[-1]
    assert entry["execution_status"] == "information"
    assert entry["activity_kind"] == "examination"
    assert entry["elapsed_minutes"] == clinical_time.ACTIVE_MINUTES["examination_region"]
    assert entry["response_time_min"] - entry["decision_time_min"] == entry["elapsed_minutes"]
    assert entry["learner_input"].startswith("Examine:")
    assert entry["information_obtained"]
    # It is recorded as an activity, never numbered as a decision, and nothing
    # here calls the interval an error.
    assert entry["interpreted_action"] == []
    assert entry["reasoning_gate"]["status"] == "not_required"
    assert "state_before" in entry and "state_after" in entry


# --- a sequence the resident stated is a sequence the engine keeps -----------

SEQ_REASON = (" Creo que es una neumonia grave. Espero que mejore la perfusion. "
              "Reevaluo presion y saturacion en 5 minutos.")


@pytest.mark.parametrize("text", [
    "Pido un lactato y espero el resultado, luego doy ceftriaxona 2 g EV.",
    "Pido un lactato. Cuando llegue, entonces doy ceftriaxona 2 g EV.",
    "Pido un lactato. Tras el resultado, entonces doy ceftriaxona 2 g EV.",
    "Order a lactate and wait for the result, then give ceftriaxone 2 g IV.",
])
def test_an_order_told_to_wait_for_a_result_says_so(engine, text):
    parsed = engine["clinical_interpreter"](text + SEQ_REASON)
    treatment = next(a for a in parsed["actions"] if a["type"] == "antibiotics")
    assert treatment["after_result"] == "lactate"


@pytest.mark.parametrize("text", [
    "Doy oxigeno por mascarilla de no reinhalacion 15 L/min y luego reevaluo en 10 minutos.",
    "Doy ceftriaxona 2 g EV y luego pido un lactato.",
    "Give ceftriaxone 2 g IV, then reassess in 10 minutes.",
])
def test_merely_sequencing_two_orders_is_not_a_dependency(engine, text):
    parsed = engine["clinical_interpreter"](text + SEQ_REASON)
    assert not any(a.get("after_result") for a in parsed["actions"]), text


def test_the_held_order_does_not_run_until_its_result_is_back(engine):
    session, results = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un panel de laboratorio y espero el resultado, luego doy ceftriaxona 2 g EV."
        + SEQ_REASON])
    assert session["state"]["treatments"].get("administered_medications", []) == []
    held = [s for s in results[0]["action_summaries"] if s.get("type") == "deferred"]
    assert held and "Held as instructed until basic labs is back" in held[0]["label"]
    assert "expected at 10 min" in held[0]["label"]
    assert family_engine.deferred_orders(session["state"])[0]["after_result"] == "basic_labs"


def test_it_runs_at_the_minute_the_result_arrives(engine):
    session, results = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un panel de laboratorio y espero el resultado, luego doy ceftriaxona 2 g EV."
        + SEQ_REASON,
        "Reevalua saturacion en 5 minutos.",
        "Reevalua saturacion en 8 minutos."])
    assert len(session["state"]["treatments"]["administered_medications"]) == 1
    given = session["state"]["treatments"]["administered_medications"][0]
    assert given["time_min"] >= 10, "not before the result it was told to wait for"
    assert family_engine.deferred_orders(session["state"]) == []


def test_the_engine_does_not_reorder_it_to_be_helpful(engine):
    """The same two orders without the instruction run at once; with it they do not."""
    together, _ = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un panel de laboratorio y doy ceftriaxona 2 g EV." + SEQ_REASON])
    assert len(together["state"]["treatments"]["administered_medications"]) == 1
    sequenced, _ = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un panel de laboratorio y espero el resultado, luego doy ceftriaxona 2 g EV."
        + SEQ_REASON])
    assert sequenced["state"]["treatments"].get("administered_medications", []) == []


def test_a_held_order_runs_exactly_once(engine):
    session, _ = play(engine, "pneumonia", "pneumonia_46f", [
        "Pido un lactato y espero el resultado, luego doy ceftriaxona 2 g EV." + SEQ_REASON,
        "Reevalua saturacion en 10 minutos.",
        "Reevalua saturacion en 10 minutos.",
        "Reevalua saturacion en 10 minutos."])
    assert len(session["state"]["treatments"]["administered_medications"]) == 1


def test_a_held_order_still_answers_for_its_reasoning(engine):
    """Waiting for a result does not excuse a management order from the four."""
    parsed = engine["clinical_interpreter"](
        "Pido un lactato y espero el resultado, luego doy ceftriaxona 2 g EV.")
    assert engine["reasoning_gate_missing"](parsed) == [
        "working_model", "expected_effect", "reassessment_target"]
