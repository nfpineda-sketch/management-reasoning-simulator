"""How a Chilean resident writes an order, and what happens when it is not read.

Found playing all twenty-one bank variants in Spanish (2026-09-21). Each case
below cost a real turn in that session: the route the resident had already
written was asked for again, a flow written in words was not a flow, the
resuscitation bag had one spelling out of four, a reservoir mask executed as a
simple mask, and a pacemaker ordered with "instala" disappeared from the record
without a word. English phrasing is untouched.
"""
import pytest

from family_parser import parse_family_actions
from pending_family_orders import complete_bundle, hold_incomplete_bundle


def actions(text):
    return parse_family_actions(text)["actions"]


def first(text, kind):
    return next((a for a in actions(text) if a.get("type") == kind), None)


# "Endovenoso" is the ordinary word for this route here.

@pytest.mark.parametrize("text", [
    "Administra 25 g de glucosa endovenosa.",
    "Administra 25 g de glucosa por via endovenosa.",
    "Administra naloxona 0.4 mg e.v.",
    "Administra naloxona 0.4 mg i.v.",
])
def test_the_intravenous_route_is_read_as_it_is_written(text):
    given = [a for a in actions(text) if a.get("type") in {"dextrose", "naloxone"}]
    assert given and given[0].get("route") == "IV", actions(text)


# A flow spoken in words is the same flow.

@pytest.mark.parametrize("text, flow", [
    ("Ponle oxigeno por naricera a 4 litros por minuto.", 4.0),
    ("Ponle oxigeno por naricera a 4 litros.", 4.0),
    ("Ponle oxigeno por naricera a 4 L/min.", 4.0),
])
def test_a_flow_written_in_words_is_a_flow(text, flow):
    assert first(text, "oxygen") == {"type": "oxygen", "device": "nasal cannula", "flow_lpm": flow}


# The bag, under the names it is given at the bedside.

@pytest.mark.parametrize("text", [
    "Ventila con bolsa-mascara.",
    "Ventila con bolsa-mascarilla.",
    "Ventila con ambu.",
    "Ventila con bolsa de reanimacion.",
])
def test_the_resuscitation_bag_has_more_than_one_name(text):
    assert first(text, "bag_mask") is not None, actions(text)


# A reservoir mask used to execute as a simple mask, silently.

@pytest.mark.parametrize("text", [
    "Ponle mascarilla de recirculacion a 15 L/min.",
    "Ponle mascarilla con reservorio a 15 L/min.",
    "Ponle mascara de reservorio a 15 litros.",
])
def test_a_reservoir_mask_is_not_a_simple_mask(text):
    assert first(text, "oxygen")["device"] == "non-rebreather mask"


def test_a_bare_mask_is_still_the_simple_mask():
    assert first("Ponle una mascara a 8 L/min.", "oxygen")["device"] == "simple mask"


# "Instalar" is how a device is ordered here. Without the verb the clause had
# no verb at all, and a clause with no verb was dropped without a word.

def test_a_device_ordered_with_instalar_is_an_order():
    assert first("Instala naricera a 4 litros por minuto.", "oxygen") == {
        "type": "oxygen", "device": "nasal cannula", "flow_lpm": 4.0}
    niv = first("Instala VMNI con IPAP 14, EPAP 6 y FiO2 50%.", "niv")
    assert (niv["ipap_cmh2o"], niv["epap_cmh2o"], niv["fio2_percent"]) == (14.0, 6.0, 50.0)


@pytest.mark.parametrize("text", [
    # This list keeps shrinking as faculty decisions land: the pacemaker became a
    # real order with decision 5, and the nursing orders with decision 13. What
    # matters is that whatever is still unsupported is quoted back, not dropped.
    "Instala un cateter de arteria pulmonar.",
    "Instala un balon de contrapulsacion intraaortico.",
    "Administra dopamina 5 mcg/kg/min.",
])
def test_an_unsupported_order_is_quoted_back_instead_of_vanishing(text):
    parsed = actions(text)
    assert parsed, "the order disappeared from the record"
    assert parsed[0]["type"] == "clarification"


# One submission that names the same panel twice orders it once.

def test_two_names_for_one_panel_are_one_sample():
    studies = [a for a in actions("Pide hemograma y electrolitos.") if a["type"] == "diagnostic"]
    assert studies == [{"type": "diagnostic", "diagnostic": "basic_labs"}]


# The airway order as it is spoken: intubate and connect, in one sentence.

def test_connecting_the_ventilator_is_part_of_the_airway_order():
    parsed = actions("Intuba con secuencia rapida y conecta en VC/AC con FiO2 100%, "
                     "PEEP 5, volumen corriente 6 mL/kg y frecuencia 12.")
    assert [a["type"] for a in parsed] == ["intubation"], parsed
    assert parsed[0]["ventilator_mode"] == "VC/AC"
    assert parsed[0]["fio2_percent"] == 100.0
    assert parsed[0]["peep_cmh2o"] == 5.0
    assert parsed[0]["tidal_ml_per_kg"] == 6.0
    assert parsed[0]["rate_per_min"] == 12.0


def test_a_tidal_volume_per_kilo_is_never_a_fluid_bolus():
    parsed = actions("Intuba y conectalo a ventilacion mecanica en VC/AC con FiO2 100%, "
                     "PEEP 5 y volumen corriente 6 mL/kg.")
    assert not [a for a in parsed if a["type"] == "fluid"], parsed


# A held order asked for the route. The next whole turn is not that answer.

def held_bundle(text):
    parsed = parse_family_actions(text)
    return hold_incomplete_bundle(parsed)


def test_a_new_turn_supersedes_a_held_order_instead_of_completing_it():
    # Found in the hypoglycaemia case: "the oral drug lasts hours" set the route
    # of the held dextrose to PO, and in the opioid case the held 0.04 mg was
    # completed with the route of a turn that asked for 0.1 mg.
    pending = held_bundle("Administra 25 g de glucosa.")
    reply = ("Mejoro con el bolo, pero el hipoglicemiante oral dura horas debido a la "
             "insuficiencia renal. La prioridad ahora es prevenir la recurrencia. "
             "Reevalua en 60 minutos glicemia y estado mental.")
    assert complete_bundle(pending, reply) == {"superseded": True}


def test_an_answer_to_the_question_still_completes_the_held_order():
    pending = held_bundle("Administra 25 g de glucosa.")
    resolved = complete_bundle(pending, "IV")
    assert resolved["parsed"]["actions"][0]["route"] == "IV"
    pending = held_bundle("Ponle oxigeno.")
    resolved = complete_bundle(pending, "naricera a 4 L/min")
    assert resolved["parsed"]["actions"][0]["flow_lpm"] == 4.0


# "Dejar" carries two different orders depending on what follows it.

def test_leaving_an_indication_and_stopping_an_infusion_are_told_apart():
    # "Deja regimen cero" became a supported nursing order with decision 13.
    assert actions("Deja regimen cero.")[0]["type"] == "npo"
    assert first("Deja de pasar el suero.", "fluid")["operation"] == "stop"
    assert first("Deja de administrar la noradrenalina.", "norepinephrine")["operation"] == "stop"
