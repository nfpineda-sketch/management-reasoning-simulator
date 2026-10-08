"""The room's response cards say the engine's orders in Spanish, whole (faculty, 2026-09-26).

Found in the Spanish rehearsal of scenario 19 (2026-09-27): a card read "Tras
suero fisiológico 1000 mL IV started as a bolus (no rate written; ...)" and
"Epinephrine inicio at 0.1 mcg/kg/min", because the generic words translated
the engine's labels by halves. One sample per label the engine writes (family
engine, the response card), each said with no English word left; drug names,
doses and units stay as the engine writes them (decision 16).
"""
import re

import pytest

import language

SAMPLES = (
    "Synchronized cardioversion delivered: 100 J",
    "stopping crystalloid (400 mL not given)", "withholding further fluid (none was running)",
    "normal saline 1000 mL IV started",
    "normal saline 1000 mL IV started as a bolus (no rate written; the simulator's standard rate, about 50 mL/min)",
    "normal saline 1000 mL IV started (400 mL of 1000 mL infused by 12 min; remainder due at 30 min)",
    "Lactate reviewed; the result already on file is unchanged",
    "Troponin has been requested and is not back yet; it is expected at 45 min",
    "Troponin has not been requested in this encounter",
    "Tourniquet applied to the left thigh: the external bleeding is controlled",
    "Direct pressure applied to the scalp: there is no external source bleeding here",
    "Pelvic binder applied at the greater trochanters; the pelvic volume is reduced",
    "Epinephrine 50 mcg IV bolus", "Nitroglycerin 400 mcg IV bolus",
    "Continuous nebulized salbutamol running at 10 mg/h; unchanged",
    "Continuous nebulized salbutamol adjusted to 15 mg/h", "Continuous nebulized salbutamol 10 mg/h started",
    "Norepinephrine start at 0.1 mcg/kg/min", "Norepinephrine adjust at 0.2 mcg/kg/min", "Norepinephrine stop",
    "urinary catheter removed", "urinary catheter already in place; not repeated", "urinary catheter placed",
    "peripheral intravenous access placed", "peripheral intravenous access already in place; not repeated",
    "propofol infusion started at 2 mg/kg/h", "fentanyl infusion adjusted to 50 mcg/h; this is analgesia, not sedation",
    "atropine 0.5 mg IV administered; the atrial rate rises and the ventricular escape does not follow",
    "Oral carbohydrate given", "Dextrose 10% at 50 mL/h started", "Naloxone infusion at 0.4 mg/h started",
    "alteplase 50 mg IV given", "alteplase 50 mg IV given: the artery is already open",
    "tenecteplase 40 mg IV given: reperfusion is expected at minute 55",
    "tenecteplase 40 mg IV given: this ECG shows no occlusion pattern, so thrombolysis carries its bleeding risk "
    "without an artery to open",
    "Exercise stress test started", "Exercise stress test performed: no ischaemic change at the workload achieved",
    "Needle decompression of the left chest: no air under tension was released",
    "Needle decompression of the right chest: the pneumothorax is on the other side",
    "Finger decompression of the left chest: air under tension released; the pressure and the saturation recover",
    "Chest tube in the left chest: 1100 mL of blood drained immediately and it continues to fill",
    "Needle decompression of the left chest: no air under tension was released. A haemothorax is drained with a "
    "tube, not a needle",
    "Ventilator circuit disconnected; the chest is allowed to empty", "Ventilator settings: VC/AC, FiO2 60%, PEEP 8",
    "Intubation completed; invasive ventilation started", "Bag-mask assisted ventilation started",
    "Discharge home already requested; not repeated", "ED observation for 6 h ordered; the period has not been completed",
    "Admission to ICU already requested; not repeated", "Transfer/admission requested: ICU",
    "After requesting admission to ICU, BP 147/83 mmHg", "After discharging the patient home, BP 120/80 mmHg",
    "cardiology already contacted (not repeated)", "Airway equipment prepared; intubation has not occurred",
    "Epinephrine start at 0.1 mcg/kg/min (0.1 mcg/kg/min × 115 kg = 11.5 mcg/min, actual body weight, reported by "
    "his wife; engine convention while the weight type for this drug is undecided)",
)
ENGLISH = re.compile(
    r"\b(?:the|and|with|was|started|as|rate|written|about|requested|given|over|at|minute|after|for|of|to|is|not|"
    r"already|repeated|stopping|withholding|running|adjusted|unchanged|reviewed|result|file|applied|bleeding|"
    r"controlled|delivered|removed|placed|stopped|contacted|requesting|admission|discharging|patient|home|"
    r"decompression|chest|released|settings|bolus|infusion|start|adjust|administered|open|artery|tension|air|"
    r"engine|convention|weight|undecided|ordered|period|completed|expected|back|stop)\b")


@pytest.mark.parametrize("english", SAMPLES)
def test_an_engine_order_is_said_whole_in_spanish(english):
    spanish = language.say(english, "es")
    assert not ENGLISH.findall(spanish), spanish


def test_what_the_engine_writes_stays_as_written():
    spanish = language.say("After normal saline 1000 mL IV started as a bolus (no rate written; the simulator's "
                           "standard rate, about 50 mL/min) + Epinephrine 0.5 mg IM administered, BP 77/42 mmHg", "es")
    # The drug by its Spanish name (V-9, faculty, 2026-10-07; B-5, IG-5); the dose and the route as written.
    assert spanish == ("Tras suero fisiológico 1000 mL IV iniciado en bolo (sin velocidad escrita; velocidad estándar "
                       "del simulador, unos 50 mL/min) + Adrenalina 0.5 mg IM administrado, PA 77/42 mmHg")
    assert language.say("Tourniquet applied to the left thigh: the external bleeding is controlled", "es") == (
        "Torniquete aplicado en el muslo izquierdo: el sangrado externo está controlado")
    for sample in SAMPLES:
        assert language.say(sample, "en") == sample


MORE = (
    "While awaiting diagnostic results over 2 minutes, BP 68/44 mmHg",
    "After cath lab already contacted (not repeated), BP 95/61 mmHg",
    "After contacting ICU (no intervention yet), BP 142/86 mmHg",
    "**Working model:** shock  \n**Management priority:** perfusion  \n**Expected effect:** BP  \n"
    "**Reassessment:** PA in 30 minutes",
    "Indicated and recorded as your decision: doy ondansetron 4 mg ev. Its administration and effect are not "
    "modelled in this simulator, so nothing was given and nothing changed.",
    "Prescription for home recorded: indico autoinyector al alta. It is a prescription, not a dose given here.",
    "Recorded as a conditional plan, not executed now: doy de alta si la tolera.",
    "Recorded as advice to the patient: regresar si tiene fiebre.",
    "Right-sided leads V3R and V4R, recorded alongside the standard twelve. ST elevation of 1.5 mm in V4R, with 1 mm "
    "in V3R. The inferior elevation is unchanged in this tracing. Textual report: this encounter records the "
    "additional leads in words; the rendered tracing shows the standard twelve.",
    "The fluid was given faster than the obstructed right ventricle can accept: it distends, the septum shifts and "
    "the output falls. Volume here is given slowly and in small amounts, or not at all.",
)


@pytest.mark.parametrize("english", MORE)
def test_the_room_s_other_fixed_sentences_are_said_whole(english):
    spanish = language.say(english, "es")
    assert not ENGLISH.findall(spanish), spanish


def test_what_the_resident_wrote_is_quoted_not_translated():
    spanish = language.say("Recorded as advice to the patient: regresar si tiene fiebre.", "es")
    assert spanish == "Registrado como indicación al paciente: «regresar si tiene fiebre»."


@pytest.mark.parametrize("english, spanish", [
    ("Respiratory rate: 34/min. Work of breathing: Markedly increased",
     "Frecuencia respiratoria: 34/min. Trabajo respiratorio: muy aumentado"),
    ("Capillary refill: 4 s. Extremities: Cool", "Llene capilar: 4 s. Extremidades: frías"),
    ("Pulse absent. Capillary refill is not measurable.", "Pulso ausente. El llene capilar no es medible."),
    ("Capillary refill 3 s; extremities cool.", "Llene capilar 3 s; extremidades frías."),
    ("Mental status: Drowsy. Expression: uncomfortable. Color: mild pallor. Diaphoresis: marked. "
     "Mottling on visible extremities.",
     "Estado mental: Somnoliento. Expresión: incómoda. Color: palidez leve. Diaforesis: marcada. "
     "Moteado en las extremidades visibles."),
])
def test_an_examination_finding_the_engine_composes_is_said_whole(english, spanish):
    assert language.examination(english, "es") == spanish
    assert language.examination(english, "en") == english


def test_the_neurological_finding_quotes_the_case_s_approved_words_only():
    import case_text
    neuro = case_text.passages()["hypoglycemia_28m"]["/examination/Neurological"]
    engine = ("Current mental status: Drowsy. Engagement is reduced; interpret alongside respiratory and "
              "circulatory findings. Pupils are equal and reactive.")
    language.set_narrative({})
    try:
        # Not approved: the engine's words in Spanish, the case's own words as the case says them.
        assert language.examination(engine, "es", case="hypoglycemia_28m").endswith("Pupils are equal and reactive.")
        language.set_narrative({"hypoglycemia_28m": {neuro["en"]: neuro["es"]}})
        spanish = language.examination(engine, "es", case="hypoglycemia_28m")
        assert spanish.startswith("Estado mental actual: somnoliento.")
        assert spanish.endswith("Pupilas isocóricas y reactivas.") and "Moviliza" not in spanish
    finally:
        language.set_narrative({})


def test_a_fixed_message_among_the_history_answers_is_said_whole():
    english = "I couldn't match that question to the recorded history. Please rephrase it or use History topics."
    assert language.case_words(english, "es").startswith("No pude relacionar esa pregunta")
    assert language.case_words(english, "en") == english
