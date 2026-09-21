"""Spanish orders written in the imperative, and goals that contain a verb.

In local testing "Inicia BiPAP ..." and "Inicia nitroglicerina ..." were dropped
without a clarification, because the interpreter knew only "iniciar" and
"inicie". In the same entry "Mi prioridad es la oxigenación y bajar precarga y
poscarga" was cut to "oxigenación": "bajar" ended the priority as if it began a
new order.
"""
import pytest

from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine

REPORTED = (
    "Probable edema pulmonar agudo cardiogénico hipertensivo. "
    "Mi prioridad es la oxigenación y bajar precarga y poscarga. "
    "Inicia BiPAP IPAP 10 EPAP 5 FiO2 60%. Inicia nitroglicerina en infusión 100 mcg/min. "
    "Administra furosemida 80 mg IV. "
    "Espero SpO2 sobre 92%, menor trabajo respiratorio y PAS bajo 140. "
    "Reevalúa en 10 minutos PA, SpO2, FR y trabajo respiratorio."
)


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def test_the_reported_imperative_entry_keeps_every_order():
    actions = parse_family_actions(REPORTED)["actions"]
    assert [a["type"] for a in actions] == ["niv", "nitroglycerin", "diuretic", "reassessment"]
    niv, nitro, diuretic, reassess = actions
    assert (niv["ipap_cmh2o"], niv["epap_cmh2o"], niv["fio2_percent"]) == (10.0, 5.0, 60.0)
    assert nitro["rate_mcg_min"] == 100.0
    assert (diuretic["agent"], diuretic["dose_mg"], diuretic["route"]) == ("furosemide", 80.0, "IV")
    assert reassess["delay_min"] == 10.0


@pytest.mark.parametrize("imperative, infinitive", [
    ("Inicia", "Iniciar"), ("Inicie", "Iniciar"), ("Comienza", "Iniciar"),
    ("Suspende", "Suspender"), ("Aumenta", "Aumentar"), ("Pide", "Pedir"),
    ("Pon", "Poner"), ("Administra", "Administrar"),
])
def test_an_imperative_reads_as_its_infinitive(imperative, infinitive):
    body = {
        "Iniciar": " nitroglicerina 50 mcg/min", "Suspender": " la nitroglicerina",
        "Aumentar": " nitroglicerina a 100 mcg/min", "Pedir": " lactato y gases venosos",
        "Poner": " 500 mL de ringer lactato", "Administrar": " furosemida 40 mg IV",
    }[infinitive]
    assert parse_family_actions(imperative + body) == {
        **parse_family_actions(infinitive + body), "raw_text": imperative + body}


def test_an_imperative_later_in_a_chain_is_still_an_order():
    actions = parse_family_actions("Aumenta la FiO2 a 80%, pide gases venosos y lactato.")["actions"]
    assert [a.get("diagnostic") for a in actions if a["type"] == "diagnostic"] == ["vbg", "lactate"]


def test_a_word_inside_a_clause_is_not_rewritten():
    # Only a clause-initial verb is an order: "da" and "continua" here are not.
    from family_parser import _ES_IMPERATIVE, _ES_IMPERATIVE_FORMS
    text = "furosemida que da respuesta, infusion continua de nitroglicerina"
    rewritten = _ES_IMPERATIVE.sub(lambda m: m.group(1) + _ES_IMPERATIVE_FORMS[m.group(2)], text)
    assert rewritten == text


def test_the_reported_reasoning_keeps_the_whole_priority_and_target(engine):
    reasoning = engine["extract_explicit_reasoning"](REPORTED)
    assert reasoning["problem_representation"] == "edema pulmonar agudo cardiogénico hipertensivo"
    assert reasoning["management_priority"] == "oxigenación y bajar precarga y poscarga"
    assert reasoning["expected_effect"] == "SpO2 sobre 92%, menor trabajo respiratorio y PAS bajo 140"
    assert reasoning["reassessment_target"] == "PA, SpO2, FR y trabajo respiratorio"


@pytest.mark.parametrize("text, priority", [
    ("Mi prioridad es la perfusión y dar 1000 mL de suero.", "perfusión"),
    ("Mi prioridad es la oxigenación, inicia BiPAP.", "oxigenación"),
    ("Mi prioridad es bajar la presión arterial.", "bajar la presión arterial"),
    ("Mi prioridad es la ventilación y aumentar la FiO2 a 80%.", "ventilación"),
])
def test_an_order_still_ends_the_priority_but_a_physiological_goal_does_not(engine, text, priority):
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == priority


# "La prioridad ahora es..." is how it is written in the note, and only "mi"
# was read (found by playing the oedema case, 2026-09-21). English already
# accepted both "my" and "the".

@pytest.mark.parametrize("text, priority", [
    ("La prioridad es el nivel de cuidado adecuado.", "nivel de cuidado adecuado"),
    ("La prioridad ahora es descargar el ventrículo.", "descargar el ventrículo"),
    ("El objetivo es tratar la infección.", "tratar la infección"),
    ("Nuestra prioridad es llenar antes de apretar.", "llenar antes de apretar"),
    # The forms that already worked keep working.
    ("Mi prioridad es tratar la infección.", "tratar la infección"),
    ("Prioridad: llenar antes de apretar.", "llenar antes de apretar"),
])
def test_the_priority_is_read_with_any_of_its_determiners(engine, text, priority):
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == priority


@pytest.mark.parametrize("text", [
    "Dale furosemida 40 mg IV.",
    "La paciente tiene prioridad en el triage.",
])
def test_no_priority_is_invented(engine, text):
    assert "management_priority" not in engine["extract_explicit_reasoning"](text)


# Where a priority ends. Found in the trace of an oedema run: the recorded
# priority read "recuperar presión de perfusión sin inun", cut inside the word
# because "dar" matched inside "inundar".

@pytest.mark.parametrize("text, priority", [
    ("Prioridad: recuperar presión de perfusión sin inundar el pulmón. Inicia noradrenalina.",
     "recuperar presión de perfusión sin inundar el pulmón"),
    ("Mi prioridad es que el paciente pueda sentarse sin ahogarse. Dale furosemida 40 mg IV.",
     "que el paciente pueda sentarse sin ahogarse"),
    # The enclitic imperative ends it, with or without its written accent.
    ("Mi prioridad es la perfusión, dale 1000 mL de suero.", "perfusión"),
    ("La prioridad ahora es la oxigenación, ponle mascarilla a 10 L/min.", "oxigenación"),
    ("Mi prioridad es tratar la infección, cárgale ceftriaxona 2 g IV.", "tratar la infección"),
    ("La prioridad ahora es titular el vasopresor, súbele la infusión a 0.1 mcg/kg/min.",
     "titular el vasopresor"),
    ("Mi prioridad es llenar antes de apretar, pásale 1000 mL de suero.", "llenar antes de apretar"),
])
def test_the_priority_ends_at_an_order_and_not_inside_a_word(engine, text, priority):
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == priority
