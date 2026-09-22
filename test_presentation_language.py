"""The language the encounter is presented in.

Faculty decision 16 of 2026-09-21, from the full bank review. A resident wrote
in Spanish and everything answered in English, including sentences that mixed
the two. The decision separates the language of input, which is already both,
from the language of presentation, which is a setting, from the resident's own
words, which are never rewritten.
"""
import pytest

import language
from family_parser import parse_family_actions


def test_english_is_unchanged_and_is_the_default():
    assert language.DEFAULT == "en"
    text = "After 30 minutes, BP 96/60 mmHg · HR 108/min. Drowsy; capillary refill 4.0 s."
    assert language.say(text, "en") == text


def test_the_response_card_is_read_in_spanish():
    said = language.say("After Naloxone 0.4 mg IV + Simple mask at 10 L/min, BP 106/64 mmHg · "
                        "HR 68/min · SpO₂ 99% · RR 12/min. Alert; respiratory effort normal; "
                        "capillary refill 2 s. The patient reports severe pain.", "es")
    assert "PA 106/64 mmHg" in said and "FC 68/min" in said and "FR 12/min" in said
    assert "Alerta" in said and "llene capilar 2 s" in said
    assert "El paciente refiere dolor intenso" in said


def test_numbers_doses_units_and_drug_identity_survive_the_change():
    original = "After aspirin 300 mg PO administered + cath lab activated, BP 84/55 mmHg · HR 42/min."
    said = language.say(original, "es")
    # The decision is explicit: what a language change may not touch.
    for token in ("aspirin", "300 mg", "PO", "84/55 mmHg", "42/min"):
        assert token in said, token


def test_a_held_order_says_the_same_thing_in_both_languages():
    held = ("**ORDER HELD — CLARIFICATION REQUIRED** I understood: **Troponin**. Nothing in this "
            "order was executed and the patient state has not changed.")
    said = language.say(held, "es")
    assert "ORDEN RETENIDA" in said and "Entendí:" in said
    assert "no ha cambiado" in said


@pytest.mark.parametrize("english, fragment", [
    ("Complete atrioventricular block: the inferior infarct has taken the AV node. The rate falls "
     "and the pressure falls with it.", "Bloqueo auriculoventricular completo"),
    ("85 mL of urine collected between minute 30 and minute 60 (about 169 mL/h).",
     "Se recolectaron 85 mL de orina"),
    ("The requested study was not recognized.", "El examen solicitado no se reconoció"),
])
def test_the_engine_speaks_spanish_where_it_has_been_taught_to(english, fragment):
    assert fragment in language.say(english, "es")


def test_an_untaught_sentence_stays_readable_instead_of_breaking():
    # Anything without a rule is still shown, in English, rather than lost.
    odd = "A sentence the catalogue has never seen."
    assert language.say(odd, "es") == odd


def test_the_same_order_acts_the_same_whichever_language_it_is_written_in():
    spanish = parse_family_actions("Administra aspirina 300 mg VO.")["actions"]
    english = parse_family_actions("Give aspirin 300 mg PO.")["actions"]
    assert spanish == english


def test_the_monitor_labels_are_read_in_spanish():
    assert language.say("BP · MAP", "es") == "PA · PAM"
    assert language.say("MENTAL STATUS", "es") == "ESTADO MENTAL"
    assert language.say("BP: 84/55 mmHg", "es") == "PA: 84/55 mmHg"


def test_the_environment_can_choose_the_language_for_a_headless_run(monkeypatch):
    monkeypatch.setenv("MRS_LANGUAGE", "es")
    assert language.configured() == "es"
    monkeypatch.setenv("MRS_LANGUAGE", "klingon")
    assert language.configured() == "en"
