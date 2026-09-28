"""The minor debt of cycle 8: TD-23, TD-27 and TD-28 (TD-25 is a rename in test_acs_reperfusion.py)."""
import time

import pytest

import acs_reperfusion
import language
from family_parser import parse_family_actions


# --- TD-23: what the Spanish page still said in English --------------------------------------------

@pytest.mark.parametrize("lv, territory, spanish", [
    (0.9, "inferior", "La pared inferior se contrae normalmente; las demás paredes se contraen normalmente"),
    (0.75, "inferior", "La pared inferior muestra una contracción levemente disminuida; las demás paredes se "
                       "contraen normalmente"),
    (0.6, "lateral", "La pared lateral muestra una contracción moderadamente disminuida; las demás paredes se "
                     "contraen normalmente"),
    (0.3, "posterior", "La pared posterior está acinética; las demás paredes se contraen normalmente"),
    (0.75, "anterior", "La pared anterior y el ápex muestran una contracción levemente disminuida; las demás "
                       "paredes se contraen normalmente"),
    (0.3, "anterior", "La pared anterior y el ápex están acinéticos; las demás paredes se contraen normalmente"),
    (0.75, "subendocardial", "La contracción está globalmente levemente disminuida, sin un defecto focal único"),
    (0.9, "left_main", "La contracción es globalmente normal, sin un defecto focal único"),
])
def test_the_wall_motion_of_an_occlusion_is_said_whole_in_spanish(lv, territory, spanish):
    english = acs_reperfusion.wall_motion({"lv_function": lv}, {"territory": territory})
    assert language.say(english, "es") == spanish
    assert language.say(english, "en") == english


def test_the_urgent_and_override_notices_are_said_in_spanish():
    urgent = ("Urgent intervention executed without waiting for the reasoning. Not stated: what do you think is going "
              "on, what will you check, and when. You can explain it afterwards; it is recorded as a retrospective "
              "explanation.")
    assert language.say(urgent, "es") == (
        "Intervención urgente ejecutada sin esperar el razonamiento. No se indicó: qué crees que está pasando, qué "
        "vas a revisar y cuándo. Puedes explicarlo después; queda registrado como explicación retrospectiva.")
    assert language.say("Facilitator override accepted. The held order was executed with incomplete prospective "
                        "reasoning.", "es").startswith("Anulación docente aceptada. La orden retenida se ejecutó")
    assert language.say("Facilitator override accepted, but the order did not run: see the message below.",
                        "es") == "Anulación docente aceptada, pero la orden no se ejecutó: mira el mensaje de abajo."


# --- TD-27: a long run of spaces ---------------------------------------------------------------------

def test_a_long_run_of_spaces_is_read_at_once():
    text = "SF 500 ml ev" + " " * 8000 + "y ceftriaxona 2 g ev"
    start = time.perf_counter()
    parsed = parse_family_actions(text)
    assert time.perf_counter() - start < 1.0
    assert [action["type"] for action in parsed["actions"]] == ["fluid", "antibiotics"]
    # What the resident wrote is kept as written.
    assert parsed["raw_text"] == text
    # A line break still ends a sentence.
    assert [a["type"] for a in parse_family_actions("Give NS 500 mL\n\n\nReassess in 30 minutes")["actions"]] == [
        "fluid", "reassessment"]


# --- TD-28: a question quotes the order as it was written --------------------------------------------

@pytest.mark.parametrize("text, quoted", [
    ("Pasa pipetazo 4,5 g EV", "Pasa pipetazo 4,5 g EV"),
    ("Pásale xyzcilina 1 g EV", "Pásale xyzcilina 1 g EV"),
    ("Chorrea 1000 mL de suero fisiológico IV.", "Chorrea 1000 mL de suero fisiológico IV"),
])
def test_a_question_quotes_the_order_as_it_was_written(text, quoted):
    action = parse_family_actions(text)["actions"][0]
    assert action["unrecognized_text"] == quoted
    assert f'"{quoted}"' in action["message"]
