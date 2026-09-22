"""Units written out in words, and the one volume the patient produces.

Found playing the left main case in Spanish (2026-09-22). Three orders were
lost or held over wording that is ordinary at the bedside:

  "fentanilo 50 microgramos"                 -> the dose was dropped and the
                                                engine asked for milligrams
  "noradrenalina 0,1 microgramos por kilo
   por minuto"                               -> the rate and its units were lost
  "... con diuresis de 54 mL/h" (a finding)  -> quoted back as an unrecognized
                                                order, holding the submission

A unit spelled out is the same unit, and urine is measured, never given.
"""
import pytest

from family_parser import parse_family_actions


def only(text):
    actions = parse_family_actions(text)["actions"]
    assert len(actions) == 1, actions
    return actions[0]


# --- a unit spelled out is the same unit -----------------------------------

@pytest.mark.parametrize("spoken, symbol", [
    ("Administra fentanilo 50 microgramos endovenoso.", "Administra fentanilo 0.05 mg endovenoso."),
    ("Indica morfina 2 miligramos endovenosa.", "Indica morfina 2 mg endovenosa."),
    ("Pasa 500 mililitros de suero fisiologico endovenoso.", "Pasa 500 mL de suero fisiologico IV."),
    ("Inicia noradrenalina 0,1 microgramos por kilo por minuto endovenosa.",
     "Inicia noradrenalina 0.1 mcg/kg/min IV."),
    ("Inicia dobutamina 5 mcg por kilo por minuto endovenosa.", "Inicia dobutamina 5 mcg/kg/min IV."),
    ("Inicia nitroglicerina 20 microgramos por minuto endovenosa.",
     "Inicia nitroglicerina 20 mcg/min IV."),
])
def test_the_spoken_unit_reads_as_the_symbol(spoken, symbol):
    assert only(spoken) == only(symbol)


def test_the_microgram_is_not_asked_for_in_milligrams():
    # Fentanyl is prescribed in micrograms; asking for milligrams is backwards,
    # and the dose was being discarded in silence before the question.
    action = only("Administra fentanilo 50 microgramos endovenoso.")
    assert action["type"] == "opioid_analgesia" and action["agent"] == "fentanyl"
    assert action["dose_mg"] == pytest.approx(0.05)


def test_a_rate_in_words_keeps_its_units():
    action = only("Inicia noradrenalina 0,1 microgramos por kilo por minuto endovenosa.")
    assert action == {"type": "norepinephrine", "rate": pytest.approx(0.1),
                      "units": "mcg/kg/min", "operation": "start"}


def test_a_pacing_rate_is_not_a_unit_and_keeps_its_wording():
    # "a 70 por minuto" is beats, not a dose: only a unit immediately before the
    # "por" is rewritten, so the pacemaker still reads its own rate.
    action = only("Inicia un marcapasos transcutaneo a 70 por minuto con 50 mA.")
    assert action["rate_per_min"] == 70 and action["output_ma"] == 50


def test_an_oxygen_flow_in_litres_is_untouched():
    action = only("Inicia oxigeno 15 litros por minuto con mascarilla de recirculacion.")
    assert action == only("Inicia oxigeno 15 L/min con mascarilla de recirculacion.")
    assert action["type"] == "oxygen" and action["flow_lpm"] == 15


# --- urine is produced, not administered ------------------------------------

REPORTED = ("La presion subio a 107/69 y el llene capilar bajo a 3,1 con diuresis de 54 mL/h, "
            "debido a que el soporte esta compensando. Pide troponina de control.")


def test_a_reported_urine_output_is_not_an_order():
    assert only(REPORTED) == {"type": "diagnostic", "diagnostic": "troponin"}


@pytest.mark.parametrize("finding", [
    "Diuresis de 54 mL/h.",
    "El gasto urinario es de 20 mL/h.",
    "Debito urinario 15 mL/h.",
    "Urine output 30 mL/h.",
])
def test_the_ways_the_output_is_named(finding):
    assert parse_family_actions(finding + " Pide lactato.")["actions"] == [
        {"type": "diagnostic", "diagnostic": "lactate"}]


def test_a_volume_that_really_is_an_order_is_still_caught():
    # The safety net that quotes an unread treatment back must keep working: a
    # litre of saline with no verb is still held, not silently dropped.
    action = only("Suero fisiologico 1000 mL.")
    assert action["type"] == "clarification" and "1000 ml" in action["unrecognized_text"]


def test_the_fluid_order_itself_is_unchanged():
    assert only("Pasa 500 mL de suero fisiologico IV.") == {
        "type": "fluid", "volume_ml": 500.0, "fluid_type": "normal saline", "route": "IV"}
