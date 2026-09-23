"""The same order, written in English or in Spanish, is the same order.

The design has said so since 2026-09-21: "an order in Spanish and the same
order in English produce the same action". Saying so is not the same as being
so, and three days of playing encounters found five Spanish gaps, so this
measures it instead of trusting it.

The corpus is every kind of order the bank's cases actually need. A pair that
parses differently is a defect on whichever side is poorer -- and the first one
this found was on the **English** side: "haemoglobin", the spelling this
project's own documents are written in, was refused while "hemoglobina" was
accepted.
"""
import pytest

from family_parser import parse_family_actions


PAIRS = [
    ("Give aspirin 300 mg PO", "Doy aspirina 300 mg vo"),
    ("Give ceftriaxone 2 g IV", "Doy ceftriaxona 2 g ev"),
    ("Start oxygen via nasal cannula 4 L/min", "Inicio oxigeno por naricera a 4 L/min"),
    ("Give salbutamol 5 mg nebulized", "Doy salbutamol 5 mg nebulizado"),
    ("Give hydrocortisone 200 mg IV", "Doy hidrocortisona 200 mg ev"),
    ("Transfuse 2 units of packed red blood cells", "Transfundo 2 unidades de globulos rojos"),
    ("Give 500 mL normal saline IV bolus", "Paso suero fisiologico 500 ml ev en bolo"),
    ("Start CPAP 8 FiO2 60%", "Inicio CPAP 8 con FiO2 60%"),
    ("Start nitroglycerin infusion at 50 mcg/min", "Inicio nitroglicerina en infusion a 50 mcg/min"),
    ("Give furosemide 40 mg IV", "Doy furosemida 40 mg ev"),
    ("Give heparin 5000 units IV", "Doy heparina 5000 UI ev"),
    ("Give naloxone 0.4 mg IV", "Doy naloxona 0.4 mg ev"),
    ("Give dextrose 25 g IV", "Doy glucosa 25 g ev"),
    ("Give thiamine 100 mg IV", "Doy tiamina 100 mg ev"),
    ("Give magnesium sulfate 2 g IV over 20 minutes", "Doy sulfato de magnesio 2 g ev en 20 minutos"),
    ("Place a peripheral IV line", "Instalo una via venosa periferica"),
    ("Bag-mask ventilate with 100% oxygen", "Ventilo con bolsa mascarilla con oxigeno al 100%"),
    ("Intubate", "Intubar"),
    ("Start norepinephrine at 0.1 mcg/kg/min", "Inicio noradrenalina a 0.1 mcg/kg/min"),
    ("Give omeprazole 80 mg IV", "Doy omeprazol 80 mg ev"),
    ("Order an ECG", "Pido un electrocardiograma"),
    ("Order troponin", "Pido troponina"),
    ("Order a chest x-ray", "Pido una radiografia de torax"),
    ("Order arterial blood gases", "Pido gases arteriales"),
    ("Order POCUS", "Pido POCUS"),
    ("Order lactate", "Pido lactato"),
    ("Order haemoglobin", "Pido hemoglobina"),
    ("Order hemoglobin", "Pido hemoglobina"),
    ("Order a D-dimer", "Pido dimero D"),
    ("Order CT pulmonary angiography", "Pido angiotomografia de torax"),
    ("Order a bedside glucose", "Pido glicemia capilar"),
    ("Order blood cultures", "Pido hemocultivos"),
    ("Examine the breathing", "Examino la respiracion"),
    ("Examine the abdomen", "Examino el abdomen"),
    ("Examine the extremities", "Examino las extremidades"),
    ("Examine the neurological status", "Examino el estado neurologico"),
    ("Consult cardiology", "Consulto a cardiologia"),
    ("Consult gastroenterology", "Consulto a gastroenterologia"),
    ("Admit to the ward", "Lo hospitalizo en sala"),
    ("Admit to the ICU", "Lo hospitalizo en unidad de paciente critico"),
    ("Discharge home", "Lo mando a su casa"),
    ("Reassess in 15 minutes", "Reevaluo en 15 minutos"),
    ("Increase the nitroglycerin to 100 mcg/min", "Subo la nitroglicerina a 100 mcg/min"),
    ("Stop the nitroglycerin", "Suspendo la nitroglicerina"),
    ("Give clopidogrel 600 mg PO", "Doy clopidogrel 600 mg vo"),
    ("Give alteplase 100 mg IV", "Doy alteplasa 100 mg ev"),
]


def shape(text):
    """What the engine would do, with the wording stripped away."""
    return [(action.get("type"),
             tuple(sorted((key, value) for key, value in action.items()
                          if key != "type" and not isinstance(value, (dict, list)))))
            for action in parse_family_actions(text)["actions"]]


@pytest.mark.parametrize("english, spanish", PAIRS)
def test_the_pair_produces_the_same_action(english, spanish):
    assert shape(english) == shape(spanish)


@pytest.mark.parametrize("english, spanish", PAIRS)
def test_neither_side_is_merely_refused(english, spanish):
    # Two clarifications also match each other, which would pass the test
    # above while meaning the engine understood neither.
    for text in (english, spanish):
        kinds = [kind for kind, _ in shape(text)]
        assert kinds and "clarification" not in kinds, text


def test_the_british_spelling_of_haemoglobin_is_read():
    # The first gap this corpus found, and it was on the English side: the
    # spelling this project's documents use was the one being refused.
    assert shape("Order haemoglobin") == shape("Order hemoglobin")
