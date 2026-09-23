"""The pronoun a resident puts in front of the verb, and the orders it hid.

Found on 2026-09-23 while scripting eleven encounters for the rubric pilot.
Spanish puts the object pronoun before a conjugated verb, which is how the
closing decision is actually written: "lo hospitalizo en sala", "le doy
aspirina 300 mg vo", "la traslado a UCI". Nothing read that pronoun, so the
clause had no clause-initial verb.

Two failures, and the second is the worse one:

  * "le doy aspirina 300 mg vo" was held as an unrecognized order;
  * "lo hospitalizo en sala" and "le pido un electrocardiograma" produced no
    action and no message at all.

Silence is worse than a hold, and it fell on the disposition, which is the
whole of the continuity domain of the rubric: a domain that cannot be scored
because the order evaporated is not a resident who failed to decide.
"""
import pytest

from family_parser import parse_family_actions


def types(text):
    return [action["type"] for action in parse_family_actions(text)["actions"]]


@pytest.mark.parametrize("with_pronoun, without", [
    ("Le doy aspirina 300 mg vo", "Doy aspirina 300 mg vo"),
    ("Le paso suero fisiologico 500 ml ev", "Paso suero fisiologico 500 ml ev"),
    ("La ventilo con bolsa mascarilla", "Ventilo con bolsa mascarilla"),
    ("Le pido un electrocardiograma", "Pido un electrocardiograma"),
    ("Lo intubo", "Intubar"),
    ("Lo hospitalizo en sala", "Hospitalizar en sala"),
    ("La traslado a UCI", "Trasladar a UCI"),
    ("Lo hospitalizo en unidad de paciente critico", "Hospitalizar en unidad de paciente critico"),
])
def test_a_pronoun_before_the_verb_leaves_the_order_unchanged(with_pronoun, without):
    assert parse_family_actions(with_pronoun) == {
        **parse_family_actions(without), "raw_text": with_pronoun}


def test_the_disposition_that_was_silent_is_now_an_order():
    # The reported failure: no action and no clarification, so the record held
    # nothing at all where the resident had decided where the patient goes.
    actions = parse_family_actions("Lo hospitalizo en sala")["actions"]
    assert actions == [{"type": "disposition", "destination": "ward"}]


def test_a_pronoun_in_a_chain_is_read_like_the_first_one():
    text = "Le doy salbutamol 5 mg nebulizado y le doy ipratropio 0.5 mg nebulizado"
    assert types(text) == ["bronchodilator", "bronchodilator"]


@pytest.mark.parametrize("sentence", [
    "La saturacion sigue baja",
    "La presion arterial esta en 88/54",
    "El ingreso del paciente fue ayer",
    "El aumento del trabajo respiratorio es evidente",
    "El paso siguiente es transfundir",
    "La paciente mejoro el trabajo respiratorio",
    "Espero que baje el trabajo respiratorio",
    "Mi prioridad es broncodilatar",
    "Se queja de dolor toracico",
])
def test_an_article_before_a_noun_is_still_not_an_order(sentence):
    # "la" and "lo" are articles far more often than they are pronouns. The
    # test that decides is the word after them, read from the verb tables the
    # parser already has rather than from a list written a second time.
    assert parse_family_actions(sentence)["actions"] == []


def test_a_pronoun_rescues_the_words_that_are_also_nouns():
    # "El ingreso del paciente" is a noun phrase and stays one; "lo ingreso de
    # urgencia" is an order, and the guard that protects the first must not
    # swallow the second.
    assert parse_family_actions("Lo traslado de urgencia a UCI")["actions"] == [
        {"type": "disposition", "destination": "ICU"}]


@pytest.mark.parametrize("text, diagnostic", [
    ("Pido angiotomografia de torax", "ctpa"),
    ("Pido angioTAC de torax", "ctpa"),
    ("Pido angiotomografia pulmonar", "ctpa"),
])
def test_the_written_name_of_the_study_is_accepted_like_its_abbreviation(text, diagnostic):
    # Only "angioTAC" and "angio-TC" were listed, so the study written out in
    # full was refused as unrecognized.
    assert parse_family_actions(text)["actions"] == [
        {"type": "diagnostic", "diagnostic": diagnostic}]


def test_a_purpose_after_a_disposition_does_not_become_a_second_one():
    # "Hospitalizar en sala para continuar broncodilatadores y corticoides":
    # splitting on "y" left a bare "corticoides", which inherited the admission
    # verb, found no destination, and raised a clarification that held the whole
    # submission. The admission the resident wrote then never executed.
    assert parse_family_actions(
        "La hospitalizo en sala para continuar broncodilatadores y corticoides"
    )["actions"] == [{"type": "disposition", "destination": "ward"}]


def test_a_disposition_still_travels_with_the_orders_beside_it():
    assert types("Lo hospitalizo en UCI y consulto a cardiologia") == [
        "disposition", "consult"]


@pytest.mark.parametrize("text", [
    "La envio a su casa con indicacion de comer",
    "Lo mando a su casa",
    "Enviar a domicilio",
    "La envio a la casa",
])
def test_the_words_a_discharge_is_written_with_are_a_discharge(text):
    # "A la casa" was the only form listed. "A su casa" and "a domicilio" are
    # at least as common, and a discharge is the trigger of a defined critical
    # event: unread, the event disappears with the order.
    assert parse_family_actions(text)["actions"] == [
        {"type": "disposition", "destination": "home"}]


@pytest.mark.parametrize("sentence", ["Se fue a su casa ayer", "El paciente vive en su casa"])
def test_a_house_in_the_history_is_not_a_discharge(sentence):
    assert parse_family_actions(sentence)["actions"] == []


@pytest.mark.parametrize("text", [
    "Consulto al equipo de tromboembolismo",
    "Consulto al equipo de TEP",
    "Consulto al equipo de embolia pulmonar",
])
def test_the_embolism_team_is_asked_for_by_its_spanish_name(text):
    # The case declares involving a reperfusion-capable team as what its safe
    # management turns on, and only the English acronym was listed.
    assert parse_family_actions(text)["actions"] == [{"type": "consult", "service": "PERT"}]


def test_calling_a_service_in_the_first_person_reaches_it():
    assert parse_family_actions("Llamo a hemodinamia")["actions"] == [
        {"type": "consult", "service": "cath lab"}]
