"""Spanish orders as they are actually written, and the silence that used to follow.

Found by playing the pneumonia case in Spanish (2026-09-20). "Pasa 1000 mL de
suero fisiológico IV en 30 minutos" produced no action and no question: the
record said only "After 30 minutes" and the septic patient never received the
litre. Three changes are pinned here — the enclitic imperative ("pásale",
"ponle", "súbele"), the guard that quotes back any clause naming a substance and
an administered quantity, and the airway order that an induction agent used to
split in two.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


def actions(text):
    return parse_family_actions(text)["actions"]


@pytest.mark.parametrize("text, kind, field, value", [
    # The verb forms that lost their order in silence.
    ("Pasa 1000 mL de suero fisiológico IV en 30 minutos.", "fluid", "volume_ml", 1000.0),
    ("Pásale 500 cc de fisiológico IV.", "fluid", "volume_ml", 500.0),
    ("Pasar 1000 mL de Ringer lactato IV.", "fluid", "fluid_type", "lactated Ringer's"),
    ("Ponle oxígeno por mascarilla a 10 L/min.", "oxygen", "device", "simple mask"),
    ("Colócale una mascarilla con reservorio a 15 L/min.", "oxygen", "device", "non-rebreather mask"),
    ("Conecta a BiPAP 14/8 con FiO2 60%.", "niv", "mode", "BiPAP"),
    ("Ingrésalo a la UCI.", "disposition", "destination", "ICU"),
    ("Súbele la nitroglicerina a 100 mcg/min.", "nitroglycerin", "rate_mcg_min", 100.0),
    ("Bájale la nitroglicerina a 20 mcg/min.", "nitroglycerin", "rate_mcg_min", 20.0),
    ("Cárgale 2 g de magnesio IV.", "magnesium", "dose_mg", 2000.0),
    ("Pídele un lactato de control.", "diagnostic", "diagnostic", "lactate"),
    ("Tómale un ECG.", "diagnostic", "diagnostic", "ecg"),
])
def test_the_spanish_imperative_with_its_pronoun_is_an_order(text, kind, field, value):
    parsed = actions(text)
    assert [a["type"] for a in parsed] == [kind], parsed
    assert parsed[0][field] == value


@pytest.mark.parametrize("destination, text", [
    ("intermediate care", "Ingrésala a cuidados intermedios."),
    ("intermediate care", "Admit to the step-down unit."),
    ("ICU", "Ingrésalo a la unidad de cuidados intensivos."),
    ("ward", "Admit to the ward."),
])
def test_an_admission_names_where_the_patient_goes(destination, text):
    assert actions(text) == [{"type": "disposition", "destination": destination}]


def test_an_admission_with_no_destination_is_asked_about():
    # It used to be recorded as "Transfer/admission requested: None".
    parsed = actions("Admit the patient.")
    assert parsed[0]["type"] == "clarification"
    assert "intermediate care" in parsed[0]["message"]


def test_an_unreadable_order_with_a_dose_is_quoted_back():
    parsed = actions("Chorrea 1000 mL de suero fisiológico IV.")
    assert parsed[0]["type"] == "clarification"
    # The fragment is quoted as the parser read it: normalized, without accents.
    assert parsed[0]["unrecognized_text"] == "chorrea 1000 ml de suero fisiologico iv"
    assert "not recognized" in parsed[0]["message"]
    assert "held until then" in parsed[0]["message"]


@pytest.mark.parametrize("text", [
    # An answer to a question the engine asked, not a new order.
    "500 mL", "4 L/min", "200 J",
    # Numbers that describe rather than order.
    "La saturación es 89% y el lactato 3.8 mmol/L.",
    "Espero que la presión suba sobre 65 mmHg con 500 mL.",
    "The patient received aspirin 324 mg PO",
    "Blood pressure improved after 500 mL normal saline",
    # An order explicitly withheld stays withheld.
    "No le pases 1000 mL de suero.",
    "Give no aspirin 324 mg PO",
])
def test_the_guard_does_not_invent_a_question(text):
    assert actions(text) == []


@pytest.mark.parametrize("text", [
    "Intubate with ketamine 100 mg and volume control ventilation, FiO2 100%, PEEP 5.",
    "Intuba con ketamina 100 mg y ventilación controlada por volumen, FiO2 100%, PEEP 5.",
])
def test_an_induction_agent_does_not_split_the_airway_order(text):
    parsed = actions(text)
    assert [a["type"] for a in parsed] == ["intubation"], parsed
    assert parsed[0]["ventilator_mode"] == "VC/AC"
    assert parsed[0]["fio2_percent"] == 100.0 and parsed[0]["peep_cmh2o"] == 5.0


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


def test_the_litre_that_used_to_disappear_is_delivered(encounter):
    at = encounter
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(i for i in at.text_area if i.label == "Enter your clinical reasoning and/or actions").set_value(
        "Hipoperfusión por hipovolemia, porque el llene capilar está prolongado. Prioridad: llenar "
        "antes de apretar. Pasa 1000 mL de suero fisiológico IV en 30 minutos. Espero que suba la "
        "presión. Reevalúa en 30 minutos presión arterial y perfusión."
    )
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception
    updates = [e["text"] for e in at.session_state.events if e["kind"] == "clinical_update"]
    assert updates, [e["kind"] for e in at.session_state.events]
    assert "normal saline 1000 mL" in updates[-1], updates[-1]
    assert at.session_state.state["treatments"]["cumulative_crystalloid_ml"] == 1000


# The running treatment, named as residents name it: by its acronym or its role.
# Found in the same oedema run: "Suspende la VMNI" and "Súbele la infusión a 100
# mcg/min" were both refused, so the patient kept a support he no longer needed
# and an infusion that could not be titrated.

@pytest.mark.parametrize("text, operation", [
    ("Suspende la VMNI.", "stop"),
    ("Retira la VMNI.", "stop"),
    ("Saca la BiPAP.", "stop"),
    ("Retírale la BiPAP.", "stop"),
    ("Mantén la VMNI.", "continue"),
    ("Suspende la ventilación mecánica no invasiva.", "stop"),
])
def test_the_spanish_acronym_for_niv_is_niv(text, operation):
    parsed = actions(text)
    assert [a["type"] for a in parsed] == ["niv"], parsed
    assert parsed[0]["operation"] == operation


def test_a_named_mode_after_the_support_is_not_a_second_order():
    parsed = actions("Conéctalo a VMNI, BiPAP 14/8 con FiO2 60%.")
    assert [a["type"] for a in parsed] == ["niv"], parsed
    assert (parsed[0]["mode"], parsed[0]["ipap_cmh2o"], parsed[0]["epap_cmh2o"]) == ("BiPAP", 14.0, 8.0)


def test_two_deliberate_niv_orders_are_still_two():
    assert [(a["type"], a["operation"]) for a in actions("Suspende la BiPAP y pon CPAP 8 con FiO2 40%.")] == [
        ("niv", "stop"), ("niv", "start")]


NITRATE = {"nitroglycerin": True, "nitroglycerin_rate_mcg_min": 60.0}
TWO_INFUSIONS = {**NITRATE, "norepinephrine": True, "norepinephrine_rate": 0.05,
                 "norepinephrine_units": "mcg/kg/min"}


def resolve(text, treatments):
    from active_order_context import complete_active_order
    return complete_active_order({"treatments": treatments}, actions(text)[0])


@pytest.mark.parametrize("text", [
    "Súbele la infusión a 100 mcg/min.",
    "Increase the infusion to 100 mcg/min.",
    "Sube el goteo a 100 mcg/min.",
])
def test_the_one_running_infusion_can_be_named_by_its_role(text):
    resolved, error = resolve(text, NITRATE)
    assert error is None
    assert resolved["type"] == "nitroglycerin" and resolved["rate_mcg_min"] == 100.0


def test_stopping_the_infusion_needs_no_rate():
    resolved, error = resolve("Suspende la infusión.", NITRATE)
    assert error is None
    assert (resolved["type"], resolved["operation"]) == ("nitroglycerin", "stop")


@pytest.mark.parametrize("treatments, expected", [
    ({}, "No infusion is running. Name the drug and its starting rate."),
    (TWO_INFUSIONS, "More than one infusion is running (nitroglycerin, norepinephrine). Name the one to change."),
])
def test_the_engine_refuses_to_guess_which_infusion(treatments, expected):
    # The same rule the ventilator adjustment follows: resolve, or ask.
    assert resolve("Súbele la infusión a 100 mcg/min.", treatments)[1] == expected


def test_an_adjustment_with_no_rate_is_asked_about():
    assert resolve("Súbele la infusión.", NITRATE)[1] == "Specify the new nitroglycerin rate."


def test_naming_the_drug_still_wins_over_the_role():
    parsed = actions("Sube la nitroglicerina a 100 mcg/min.")
    assert [a["type"] for a in parsed] == ["nitroglycerin"]
    assert parsed[0]["rate_mcg_min"] == 100.0


def test_starting_an_infusion_is_not_an_adjustment():
    parsed = actions("Inicia nitroglicerina en infusión 60 mcg/min IV.")
    assert [(a["type"], a["operation"]) for a in parsed] == [("nitroglycerin", "start")]
