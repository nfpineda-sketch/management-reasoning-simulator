"""X-1 in the room: the Spanish the faculty decided, said whole (B-5, IG-5; faculty, 2026-10-07).

docs/revision/X1_ESPANOL_PROPUESTO.md holds the 105 decisions (XR-01 to XR-28). These tests hold
each group to its approved wording: the drugs by their Spanish names (V-9), the questions about an
order (X1-C01 to X1-C33, X1-R01), the reasoning gate (G-01 to G-16), the room's labels (L-01 to L-20),
the monitor, the bed space and the ECG (M-01 to M-04, E-01 to E-05), the treatments panel (T-01 to
T-13), the screens after the close (P-01 to P-07) and the internal keys cleaned in both languages
(TD-80). English stays as it was, except where the faculty changed it: XR-05 (b), the English column
of V-1, X1-C27 (e), X1-C28 and XR-18. The reader is not touched: its Spanish is in ``language``.
"""
import ast
from pathlib import Path

import pytest

import clinical_scene
import family_parser
import family_reports
import language
import pilot_acceptance as acceptance
import report_language
import report_presentation
import resuscitation_room

ROOT = Path(__file__).resolve().parent


# --- V-9 ----------------------------------------------------------------------------------------

def test_every_drug_the_reader_recognises_has_its_spanish_name():
    names = {name for agents in family_parser._AGENTS.values() for name in agents}
    assert names <= set(language.DRUG_NAMES_ES), sorted(names - set(language.DRUG_NAMES_ES))


@pytest.mark.parametrize("english, spanish", [
    ("norepinephrine", "noradrenalina"), ("Epinephrine", "Adrenalina"), ("aspirin", "aspirina"),
    ("albuterol", "salbutamol"), ("metamizole", "metamizol"), ("dextrose", "glucosa"),
    ("dextrose infusion", "suero glucosado"), ("packed red cells", "glóbulos rojos"),
    ("oral carbohydrate", "carbohidratos por vía oral"), ("tranexamic acid", "ácido tranexámico"),
    ("epinephrine_im", "adrenalina"), ("piperacillin-tazobactam", "piperacilina-tazobactam"),
])
def test_v9_names_a_drug_in_spanish_and_leaves_english_alone(english, spanish):
    assert language.drug(english, "es") == spanish
    assert language.drug(english, "en") == english
    assert language.drug("ondansetron", "es") == "ondansetron"  # a name V-9 does not carry stays as written


def test_v9_in_the_receipts_the_record_and_the_treatments_panel():
    # K-5, K-6, K-13, K-14 with the rule of X1-0: the drug in Spanish, the dose and the route as written.
    assert language.say("Executed now: **aspirin 300 mg PO**.", "es") == "Ejecutado ahora: **aspirina 300 mg PO**."
    assert language.say("Epinephrine 0.5 mg IM", "es") == "Adrenalina 0.5 mg IM"
    action = {"type": "aspirin", "agent": "aspirin", "dose_mg": 300, "route": "PO"}
    assert report_presentation.action_phrase(action) == "Aspirin 300 mg PO"
    assert report_presentation.action_phrase(action, "es") == "Aspirina 300 mg PO"
    assert action["agent"] == "aspirin"  # the canonical name stored does not change
    record = {"agent": "aspirin", "dose_mg": 300, "route": "PO", "time_min": 7}
    assert family_reports.format_administration(record) == "aspirin 300 mg PO · minute 7"
    assert family_reports.format_administration(record, "es") == "aspirina 300 mg PO · minuto 7"
    support = {"norepinephrine": True, "norepinephrine_rate": 0.1, "norepinephrine_units": "mcg/kg/min",
               "oxygen": True, "oxygen_device": "Nasal cannula", "oxygen_flow_lpm": 2}
    assert resuscitation_room.device_labels(support) == ["Nasal cannula · 2 L/min",
                                                         "Norepinephrine · 0.1 mcg/kg/min"]
    assert resuscitation_room.device_labels(support, "es") == ["Naricera · 2 L/min", "Noradrenalina · 0.1 mcg/kg/min"]


# --- X1-C01 to X1-C04, XR-05 (b), V-1 ---------------------------------------------------------------

@pytest.mark.parametrize("variant, order, english, spanish", [
    ("pneumonia_46f", "Give ceftriaxone IV.", "Please specify or confirm the ceftriaxone dose in milligrams.",
     "Indica o confirma la dosis de ceftriaxona en miligramos."),
    ("opioid_35m", "Give fentanyl IV.", "Please specify or confirm the fentanyl dose in micrograms.",
     "Indica o confirma la dosis de fentanilo en microgramos."),
    ("opioid_35m", "Start norepinephrine.", "Specify or confirm norepinephrine dose and units (mcg/min or mcg/kg/min).",
     "Indica o confirma la dosis de noradrenalina y sus unidades (mcg/min o mcg/kg/min)."),
    ("opioid_35m", "Continue aspirin.", "No aspirin is recorded as given. Specify the dose and route to start it.",
     "No hay registro de que se haya dado aspirina. Indica la dosis y la vía para iniciarlo."),
])
def test_a_dose_question_names_the_drug_the_resident_wrote(variant, order, english, spanish):
    asked = acceptance.Encounter(variant).order(order)["clarification"]
    assert asked == english
    assert language.say(asked, "es") == spanish


def test_a_class_is_named_by_its_label_never_its_key():
    assert language.class_label("beta_blocker") == "beta blocker"
    assert language.class_label("antibiotics") == "antibiotic"
    assert language.class_label("ppi") == "proton pump inhibitor"
    assert language.class_label("p2y12") == "P2Y12 inhibitor"
    assert language.class_label("procedural_sedation", "es") == "sedación para el procedimiento"
    assert language.say("Which beta blocker medication would you like to administer?", "es") == \
        "¿Qué betabloqueador quieres administrar?"
    assert language.say("Which calcium medication would you like to administer?", "es") == \
        "¿Qué sal de calcio quieres administrar?"
    assert language.say("Which procedural sedation medication would you like to administer?", "es") == \
        "¿Qué fármaco quieres usar para la sedación del procedimiento?"
    assert language.say("The specified steroid agent has no modeled response in this encounter. Please clarify the "
                        "medication.", "es") == ("El fármaco indicado como corticoide no tiene una respuesta modelada "
                                                 "en este encuentro. Aclara el fármaco.")
    source = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    assert "Which {kind} medication" not in source and "The specified {kind} agent" not in source


# --- X1-C05 to X1-C33 and X1-R01 -------------------------------------------------------------------

QUESTIONS = [
    # XR-04
    ("Specify the ventilator mode, FiO₂ as a percentage and PEEP in cm H₂O.",
     "Indica el modo del ventilador, la FiO₂ en porcentaje y la PEEP en cm H₂O."),
    ("Specify the ventilator FiO₂ as a percentage and PEEP in cm H₂O.",
     "Indica la FiO₂ del ventilador en porcentaje y la PEEP en cm H₂O."),
    ("Specify which anticoagulant, the dose and the route.", "Indica qué anticoagulante, la dosis y la vía."),
    ("Specify the output current in mA.", "Indica la corriente en mA."),
    ("Specify which side of the chest to decompress.", "Indica qué lado del tórax quieres descomprimir."),
    ("Specify CPAP or BiPAP.", "Indica CPAP o BiPAP."),
    ("Specify nasal cannula, a simple mask, a non-rebreather mask, or room air.",
     "Indica naricera, mascarilla simple, mascarilla con reservorio o aire ambiente."),
    ("Specify the oxygen flow in L/min.", "Indica el flujo de oxígeno en L/min."),
    ("Specify one quantity for the treatment to repeat.",
     "Indica una sola cantidad para el tratamiento que quieres repetir."),
    ("Specify explicit units for the quantity to repeat.", "Indica las unidades de la cantidad que quieres repetir."),
    ("Specify one target ventilator mode.", "Indica un solo modo de ventilación."),
    ("Please specify a question, investigation, treatment, or reassessment.",
     "Indica una pregunta, un examen, un tratamiento o una reevaluación."),
    ("Please restate the order.", "Escribe de nuevo la orden."),
    ("Please clarify the order before it is executed.", "Aclara la orden antes de que se ejecute."),
    # XR-15 (X1-C11 keeps its active Spanish)
    ("Specify the thrombolytic agent and dose, for example tenecteplase 40 mg IV.",
     "Indica el trombolítico y la dosis; por ejemplo, tenecteplasa 40 mg IV."),
    ("Write the total dextrose: the grams, or the concentration with the total volume. 2 ampoules with 50 mL may "
     "mean 50 mL in all or in each.",
     "Indica la glucosa total: los gramos, o la concentración con el volumen total. 2 ampollas con 50 mL pueden ser "
     "50 mL en total o en cada una."),
    # XR-07 (X1-R01, the cardioversion with «J»; X1-C14)
    ("Confirm the bolus volume in mL, up to 3000 mL per order.",
     "Confirma el volumen del bolo en mL, hasta 3000 mL por orden."),
    ("Specify the cardioversion energy in joules, from 1 to 360.", "Indica la energía de la cardioversión entre 1 y 360 J."),
    ("Specify the NIV expiratory pressure in cm H₂O, from 0 to 20.",
     "Indica la presión espiratoria de la VMNI entre 0 y 20 cm H₂O."),
    ("Specify the NIV FiO₂ as a percentage, from 21 to 100.", "Indica la FiO₂ de la VMNI entre 21 y 100 %."),
    ("Specify a tranexamic acid dose from 0.5 to 4 g.", "Indica una dosis de ácido tranexámico entre 0.5 y 4 g."),
    ("Specify an intramuscular epinephrine dose from 0.05 to 2 mg (0.5 mg is the usual adult dose).",
     "Indica una dosis de adrenalina intramuscular entre 0.05 y 2 mg (0.5 mg es la dosis habitual en adultos)."),
    ("Specify an epinephrine IV bolus from 10 to 500 mcg (50-150 mcg is the usual diluted bolus).",
     "Indica un bolo IV de adrenalina entre 10 y 500 mcg (50-150 mcg es el bolo diluido habitual)."),
    ("Specify the continuous nebulized albuterol rate in mg/h (1 to 30).",
     "Indica la velocidad de la nebulización continua de salbutamol entre 1 y 30 mg/h."),
    ("Specify a nitroglycerin IV bolus from 50 to 3000 mcg.", "Indica un bolo IV de nitroglicerina entre 50 y 3000 mcg."),
    ("Specify the dextrose infusion rate in mL/h (10 to 500).",
     "Indica la velocidad de la infusión de suero glucosado entre 10 y 500 mL/h."),
    ("Specify the naloxone infusion rate in mg/h (0.05 to 4).",
     "Indica la velocidad de la infusión de naloxona entre 0.05 y 4 mg/h."),
    ("Specify a tidal volume from 200 to 900 mL.", "Indica un volumen corriente entre 200 y 900 mL."),
    ("Specify a tidal volume from 3 to 12 mL/kg.", "Indica un volumen corriente entre 3 y 12 mL/kg."),
    ("Specify a ventilator rate from 4 to 35 breaths per minute.",
     "Indica una frecuencia del ventilador entre 4 y 35 respiraciones por minuto."),
    ("Specify an inspiratory flow from 20 to 120 L/min.", "Indica un flujo inspiratorio entre 20 y 120 L/min."),
    ("Set a pacing rate between 30 and 100 beats per minute.",
     "Indica una frecuencia del marcapasos entre 30 y 100 latidos por minuto."),
    ("Set a pacing output between 1 and 200 mA.", "Indica una corriente del marcapasos entre 1 y 200 mA."),
    # XR-12 (V-4)
    ("Name the part of the examination to perform: general appearance, breathing, peripheral perfusion, extremities, "
     "cardiac, respiratory, abdomen or neurological.",
     "Indica qué parte del examen quieres hacer: aspecto general, respiración, perfusión periférica, extremidades, "
     "cardíaco, pulmonar, abdomen o neurológico."),
    ("That examination is not available in this encounter. You may examine General appearance, Breathing or "
     "Cardiac.",
     "Ese examen no está disponible en este encuentro. Puedes examinar: Aspecto general, Respiración o Cardíaco."),
    # XR-08 (V-7)
    ("Specify the absolute target oxygen flow in L/min, not a relative change.",
     "Indica el flujo de oxígeno que quieres, en L/min, como un valor absoluto y no como un cambio relativo."),
    ("Specify absolute target ventilator settings, not a relative change.",
     "Indica los parámetros del ventilador que quieres como valores absolutos, no como un cambio relativo."),
    ("Specify a single absolute target infusion rate; a relative change or several rates is ambiguous.",
     "Indica una sola velocidad de infusión, como un valor absoluto; un cambio relativo o varias velocidades son "
     "ambiguos."),
    ("Specify nitroglycerin as an absolute infusion rate in mcg/min.",
     "Indica la nitroglicerina como una velocidad de infusión absoluta, en mcg/min."),
    ("Specify one target oxygen device and its flow in L/min (for example, nasal cannula 4 L/min, simple mask 8 L/min "
     "or non-rebreather mask 15 L/min).",
     "Indica un solo dispositivo de oxígeno y su flujo en L/min (por ejemplo, naricera 4 L/min, mascarilla simple "
     "8 L/min o mascarilla con reservorio 15 L/min)."),
    ("Specify one absolute target oxygen flow in L/min (for example, nasal cannula 4 L/min, simple mask 8 L/min or "
     "non-rebreather mask 15 L/min).",
     "Indica un solo flujo de oxígeno, como un valor absoluto en L/min (por ejemplo, naricera 4 L/min, mascarilla "
     "simple 8 L/min o mascarilla con reservorio 15 L/min)."),
    ("High-flow oxygen is not a supported device in this encounter. Specify an available oxygen device and flow (for "
     "example, nasal cannula 4 L/min, simple mask 8 L/min or non-rebreather mask 15 L/min).",
     "El oxígeno de alto flujo no es un dispositivo disponible en este encuentro. Indica un dispositivo de oxígeno "
     "disponible y su flujo (por ejemplo, naricera 4 L/min, mascarilla simple 8 L/min o mascarilla con reservorio "
     "15 L/min)."),
    ("Specify whether to start, adjust, continue, or stop NIV.",
     "Indica si quieres iniciar, ajustar, continuar o suspender la VMNI."),
    ("Specify whether to start, adjust, continue, or stop the continuous nebulization.",
     "Indica si quieres iniciar, ajustar, continuar o suspender la nebulización continua."),
    ("Specify whether to start, adjust, continue, or stop the infusion.",
     "Indica si quieres iniciar, ajustar, continuar o suspender la infusión."),
    # XR-16, XR-17, XR-19, XR-20
    ("Specify an inspiratory pressure at least as high as expiratory pressure.",
     "Indica una presión inspiratoria igual o mayor que la espiratoria."),
    ("The patient is not on a ventilator, so there is no circuit to disconnect.",
     "El paciente no está conectado a un ventilador, así que no hay un circuito que desconectar."),
    ("An intramuscular epinephrine dose is given IM or SC; for the intravenous route, order a diluted bolus or an "
     "infusion.",
     "Una dosis de adrenalina intramuscular se da IM o SC; por vía intravenosa, indica un bolo diluido o una infusión."),
    ("A diluted epinephrine bolus is given IV in this encounter.",
     "En este encuentro, un bolo diluido de adrenalina se da IV."),
    ("A nitroglycerin bolus is given IV in this encounter.", "En este encuentro, un bolo de nitroglicerina se da IV."),
    ("Specify that the cardioversion is synchronized; an unsynchronized shock is outside this encounter.",
     "Indica una cardioversión sincronizada: una descarga no sincronizada (desfibrilación) está fuera de este "
     "encuentro, en que el paciente tiene pulso."),
    ("Specify synchronized cardioversion; defibrillation is outside this pulse-present encounter.",
     "Indica una cardioversión sincronizada: una descarga no sincronizada (desfibrilación) está fuera de este "
     "encuentro, en que el paciente tiene pulso."),
    ("Cardioversion requires a pulse-present encounter.",
     "La cardioversión requiere un encuentro en que el paciente tenga pulso."),
    # XR-21
    ("That study is not one this encounter carries.", "Este encuentro no incluye ese examen."),
    ("A stress test is not an executable study in this encounter.",
     "Una prueba de esfuerzo no es un examen ejecutable en este encuentro."),
    ("Chest decompression is not an executable intervention in this encounter.",
     "La descompresión torácica no es una intervención ejecutable en este encuentro."),
    ("That neuromuscular blocker is not supported in this encounter.",
     "Ese bloqueador neuromuscular no está disponible en este encuentro."),
    ("Recognized but not executed in this build: insulin drip. Any supported actions in the same order continue "
     "separately.",
     "Esta versión reconoce, pero no ejecuta: insulin drip. Las acciones soportadas de la misma orden siguen por "
     "separado."),
    # XR-22 (the active Spanish)
    ("1000 mL at 100 mL/h would run for 10.0 h; this simulator runs a fluid order over at most 120 min. Restate it "
     "as a bolus or a shorter infusion.",
     "1000 mL a 100 mL/h durarían 10.0 h; este simulador pasa un fluido en 120 min como máximo. Escríbelo como bolo "
     "o como una infusión más corta."),
    # XR-23 (V-6), the first sentence neutral in gender
    ("Nitroglycerin was understood as a sublingual dose of 0.4 mg. This encounter gives nitroglycerin as a continuous "
     "IV infusion or an IV bolus, so nothing was converted or executed. To give it, state an infusion rate in mcg/min "
     "or an IV bolus in mcg, or say cancel.",
     "La orden de nitroglicerina se interpretó como una dosis sublingual de 0.4 mg. Este encuentro da la "
     "nitroglicerina como infusión IV continua o como bolo IV, así que no se convirtió ni se ejecutó nada. Para "
     "darla, indica una velocidad de infusión en mcg/min o un bolo IV en mcg, o di cancelar."),
    ("Norepinephrine was understood as a bolus of 10 mcg. This encounter gives norepinephrine only as a continuous "
     "IV infusion, so nothing was converted or executed. To give it, state an infusion rate in mcg/kg/min or mcg/min, "
     "or say cancel.",
     "La orden de noradrenalina se interpretó como un bolo de 10 mcg. Este encuentro da noradrenalina sólo como "
     "infusión IV continua, así que no se convirtió ni se ejecutó nada. Para darla, indica una velocidad de infusión "
     "en mcg/kg/min o mcg/min, o di cancelar."),
    # XR-09
    ("There are no pending orders to cancel.", "No hay órdenes pendientes que cancelar."),
    ("Pending orders cancelled before execution. No treatment administered; simulation time unchanged.",
     "Órdenes pendientes canceladas antes de ejecutarse. No se administró ningún tratamiento; el tiempo simulado no "
     "cambió."),
]


@pytest.mark.parametrize("english, spanish", QUESTIONS)
def test_each_question_is_said_whole_in_the_approved_spanish(english, spanish):
    assert language.say(english, "es") == spanish
    assert language.say(english, "en") == english


def test_xr18_the_oral_route_question_in_both_languages():
    asked = acceptance.Encounter("hypoglycemia_28m").order("Give 15 g of oral carbohydrate.")["clarification"]
    assert asked == ("The patient is drowsy and cannot safely swallow. Use an intravenous or intramuscular route "
                     "until oral administration is safe.")
    assert language.say(asked, "es") == ("El paciente está somnoliento y no puede tragar con seguridad. Usa una vía "
                                         "intravenosa o intramuscular hasta que sea seguro administrar por vía oral.")
    for state, said in (("obtunded", "obnubilado"), ("unresponsive", "sin respuesta")):
        assert language.say(asked.replace("drowsy", state), "es").startswith(f"El paciente está {said} y no puede")


def test_the_internal_keys_are_cleaned_in_both_languages():
    asked = acceptance.Encounter("trauma_limb_hemorrhage_27m").order("Apply a pelvic binder.")["clarification"]
    assert asked == ("The requested action (pelvic binder) is not executable in this encounter. Please clarify the "
                     "order.")
    assert language.say(asked, "es") == "La acción solicitada (faja pélvica) no es ejecutable en este encuentro. " \
                                        "Aclara la orden."
    source = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    assert "Requested study {key!r}" not in source and "; ecg. " not in source
    said = language.say("Requested study MRI brain is unavailable. Available studies: Chest X-ray, Troponin; ECG. No "
                        "orders in this submission were executed.", "es")
    assert said == ("El examen MRI brain no está disponible. Exámenes disponibles: Radiografía de tórax, Troponina; "
                    "ECG. No se ejecutó ninguna orden de esta entrega.")
    # L-17 and L-18: the headings, never the keys.
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    labels = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                  and getattr(node.targets[0], "id", "") == "_EVENT_LABELS")
    assert labels["order_cancelled"] == "ORDER CANCELLED" and labels["diagnostic"] == "ECG"
    assert language.say("ORDER CANCELLED", "es") == "ORDEN CANCELADA" and language.say("ECG", "es") == "ECG"


# --- the reasoning gate, I-10 -------------------------------------------------------------------------

def test_the_gate_and_the_held_order_summary():
    gate = ("I understood: **start norepinephrine 0.1 mcg/kg/min + 500 mL normal saline + nasal cannula 2 L/min**.\n"
            "I recognised what you want to do, what you expect to happen and what you will check.\n"
            "Still to state: what you think is going on.\n"
            "In your own words, or in the fields on screen:\n"
            "- When will you check it?\n"
            "You do not need to repeat the order. What you already wrote is kept.")
    assert language.say(gate, "es") == (
        "Entendí: **noradrenalina 0.1 mcg/kg/min (iniciado) + 500 mL suero fisiológico + oxígeno 2 L/min por "
        "naricera**.\n"
        "Reconocí qué quieres hacer, qué esperas que ocurra y qué vas a revisar.\n"
        "Todavía falta indicar: qué crees que está pasando.\n"
        "Con tus palabras o en los campos de la pantalla:\n"
        "- ¿Cuándo lo vas a revisar?\n"
        "No necesitas repetir la orden. Lo que ya escribiste se conserva.")
    assert language.say("Complete the requested reasoning to continue.", "es") == \
        "Completa el razonamiento pedido para continuar."
    # I-6 and I-10: the discarded order, by the record's labels (V-8 only where the record has none).
    assert language.say("The held order was discarded to run this one: prepare for intubation + aspirin 300 mg PO. "
                        "None of it was administered.", "es") == (
        "La orden retenida se descartó para ejecutar esta: preparar la intubación + aspirina 300 mg PO. No se "
        "administró nada de ella.")
    assert language.order_summary("start norepinephrine 0.1 mcg/kg/min", "en") == "start norepinephrine 0.1 mcg/kg/min"


# --- the room's labels ---------------------------------------------------------------------------------

LABELS = {
    # L-01, I-9, L-02 to L-08, L-10 to L-16, L-19
    "Talk": "Conversar", "Examine": "Examinar", "Tests": "Exámenes", "Treat": "Tratar", "Encounter": "Encuentro",
    "Enter your clinical reasoning and/or actions": "Ingresa tu razonamiento clínico y/o tus acciones.",
    "Ask the patient": "Pregúntale al paciente", "Ask the available history source": "Pregunta al informante disponible",
    "What brought you in today?": "¿Por qué consulta hoy?", "Ask": "Preguntar", "History topics": "Temas de la historia",
    "Explore": "Explorar", "Ask about this topic": "Preguntar por este tema",
    "Presenting symptoms and onset": "Motivo de consulta e inicio", "Examine patient": "Examinar al paciente",
    "Complete Encounter & Begin Review": "Terminar el encuentro y comenzar la revisión",
    "Save & return to dashboard": "Guardar y volver al inicio",
    "End this attempt without completing review": "Terminar este intento sin completar la revisión",
    "Current treatments": "Tratamientos en curso", "Diagnostics": "Resultados de exámenes",
    "Current support · ": "Soporte actual · ", "Resident": "Residente", "Return to dashboard": "Volver al inicio",
    "Management Reasoning Simulator · Clinical encounter v{version}":
        "Management Reasoning Simulator · Encuentro clínico v{version}",
    "The patient cannot answer at present. Questions are directed to the available collateral source.":
        "El paciente no puede responder por ahora. Las preguntas se dirigen al informante disponible.",
    # G-06 to G-11, G-14 to G-16
    "An understood order is being held. The patient state is unchanged; complete the reasoning in your own words or "
    "use the guided fields.": "Hay una orden entendida que está retenida. El estado del paciente no ha cambiado; "
                              "completa el razonamiento con tus palabras o con los campos guiados.",
    "**Held order:** {summary}": "**Orden retenida:** {summary}",
    "e.g. HR and rhythm, BP/MAP, capillary refill, mental status": "p. ej., FC y ritmo, PA/PAM, llene capilar, estado mental",
    "Complete reasoning & execute held order": "Completar el razonamiento y ejecutar la orden retenida",
    "Cancel pending orders": "Cancelar las órdenes pendientes",
    "Save retrospective explanation": "Guardar la explicación retrospectiva",
    # T-01 to T-10, T-13
    "Bag-mask assisted ventilation": "Ventilación asistida con bolsa-mascarilla",
    "Cumulative crystalloid: {volume} mL": "Cristaloide acumulado: {volume} mL",
    "Procedural sedation administered: ": "Sedación para el procedimiento: ",
    "Airway equipment and team prepared for intubation": "Equipo y personal preparados para la intubación",
    "Disposition: {destination}": "Destino: {destination}",
    "Furosemide administered: {dose} mg total": "Furosemida administrada: {dose} mg en total",
    # P-02 to P-07
    "**Expert comparison · faculty-validation draft**":
        "**Comparación con el experto · borrador pendiente de validación docente**",
    "### Attempt {number} · Carry-Forward Learning Goal": "### Intento {number} · Objetivo de aprendizaje del intento anterior",
    "**Previous attempt record · Attempt {number}**": "**Registro del intento anterior · Intento {number}**",
    "Previous PDF": "PDF anterior", "Previous Markdown": "Markdown anterior", "Previous JSON": "JSON anterior",
}


@pytest.mark.parametrize("english", list(LABELS))
def test_each_room_label_has_its_approved_spanish(english):
    assert report_language.t(english, "es") == LABELS[english]
    assert report_language.t(english, "en") == english


def test_the_monitor_the_bed_space_and_the_ecg():
    monitor = resuscitation_room.monitor_html({"hr": 90, "spo2": 95, "sbp": 120, "dbp": 70, "respiratory_rate": 20},
                                              "", language="es")
    assert "MONITOR DE CABECERA" in monitor and ">FC <" in monitor and ">PANI <" in monitor and ">FR <" in monitor
    assert "BEDSIDE MONITOR" in resuscitation_room.monitor_html({"hr": 90}, "")
    scene = clinical_scene.scene_html("aGVsbG8=", "", current=True, language="es")
    assert "Urgencias / Cama 03 · Imagen del paciente · estado actual" in scene
    assert clinical_scene.STILL_VIEW_NOTE_ES in scene and clinical_scene.STILL_VIEW_NOTE not in scene
    assert "ED / Bed 03" in clinical_scene.scene_html("aGVsbG8=", "", current=True)
    unavailable = {"state": "unavailable", "code": "NOT_ALLOWED"}
    assert clinical_scene.scene_status_text(unavailable, "es") == (
        "No hay una fotografía preparada para este encuentro. El monitor y el examen están al día.")
    assert set(clinical_scene.UNAVAILABLE_ES) == set(clinical_scene.UNAVAILABLE) - {"NO_ACCOUNTS"}
    assert resuscitation_room.ecg_words("12-lead ECG acquired. Available in ECG recordings.", "es") == \
        "ECG de 12 derivaciones tomado. Está en «Registros de ECG»."
    assert resuscitation_room.ecg_words("Acquisition", "es") == "Registro"
    assert resuscitation_room.ecg_words("Invalid heart rate.", "es") == "Frecuencia cardíaca no válida."


def test_the_treatments_panel_lines():
    assert family_reports.format_transfusion(1, 1, "es") == ("Glóbulos rojos: 1 de 2 unidades transfundidas hasta "
                                                              "ahora")
    assert family_reports.format_transfusion(1, 0, "es") == "Glóbulos rojos transfundidos: 1 unidad"
    assert family_reports.format_transfusion(2, 0, "es") == "Glóbulos rojos transfundidos: 2 unidades"
    assert family_reports.format_transfusion(2, 0) == "Packed red cells given: 2 units"
    timed = {"agent": "tranexamic acid", "dose_g": 0.5, "route": "IV", "time_min": 3, "administration_duration_min": 10,
             "administration_status": "in_progress", "ordered_dose_g": 1}
    assert family_reports.format_administration(timed, "es") == (
        "ácido tranexámico 0.5 g IV · minuto 3 · en 10 min · 0.5 de 1 g dados hasta ahora")
    assert language.say(" — started 00:15 · last adjusted 00:30", "es") == " — inicio 00:15 · último ajuste 00:30"


# --- X1-0, point 4: the documents offered in Spanish -----------------------------------------------

@pytest.fixture(scope="module")
def drugs():
    """Two drugs as the engine records them once given: their canonical names, never their Spanish ones."""
    given = acceptance.Encounter("acs_54m_inferior").order("Give aspirin 300 mg PO and start norepinephrine 0.1 "
                                                           "mcg/kg/min.")["action_summaries"]
    assert [action.get("agent") or action["type"] for action in given] == ["aspirin", "norepinephrine"]
    return given


def _words(text):
    return {word for word in ("orepinephrine", "spirin ", "oradrenalina", "spirina") if word in text}


def test_the_decision_review_record_names_its_drugs_in_spanish(drugs):
    from copy import deepcopy

    from test_curriculum_trajectories import load_engine
    from test_management_trace_report import report_example
    from test_review_record_language import pdf_text
    engine = load_engine()
    trace = deepcopy(report_example()[1]["trace"])
    trace[0]["action_summaries"] = deepcopy(drugs)
    for event in trace:
        for key in ("state_before", "state_after"):
            event[key]["case_id"] = "CE-review0001"
    prompts = engine["_review_prompt_records"](trace)
    record = engine["_review_payload"]("respiratory_distress", 14, trace, deepcopy(trace[-1]["state_after"]), prompts,
                                       {}, {}, {}, True, 1, {}, None, encounter_language="es")
    for document in (engine["_review_markdown"](record), pdf_text(engine["_review_pdf"](record))):
        assert _words(document) == {"oradrenalina", "spirina"}
    assert _words(engine["_review_markdown"](record, language="en")) == {"orepinephrine", "spirin "}
    assert trace[0]["action_summaries"] == drugs  # the canonical names it was built from are kept


def test_the_management_trace_in_the_portfolio_names_its_drugs_in_spanish(drugs):
    from management_trace_report import render_management_trace_pdf
    from test_document_language import text_of
    from test_management_trace_analysis import sample_payload, sample_report
    payload = sample_payload()
    payload["trace"][0]["action_summaries"] = [dict(action) for action in drugs]
    report = sample_report(payload)
    assert _words(text_of(render_management_trace_pdf(report, payload, language="es"))) == {"oradrenalina",
                                                                                            "spirina"}
    assert _words(text_of(render_management_trace_pdf(report, payload, language="en"))) == {"orepinephrine",
                                                                                            "spirin "}
    # The trajectory's own headings, in the words the document catalogue already holds for them.
    spanish = text_of(render_management_trace_pdf(report, payload, language="es"))
    for english, said in (("Heart rate", "Frecuencia cardíaca"), ("Systolic pressure", "Presión sistólica"),
                          ("Oxygen saturation", "Saturación de oxígeno"), ("Capillary refill", "Llene capilar")):
        assert english not in spanish and said in spanish, english


# --- what the 30-case sentinel found, with approved words (IG-5) ----------------------------------------

def test_the_pe_sentence_is_said_whole_after_its_event_label():
    for english, spanish in (
        ("The systolic pressure has stayed below 90 mmHg for 15 consecutive minutes: this is sustained hypotension "
         "from the obstruction.",
         "La presión sistólica se ha mantenido bajo 90 mmHg por 15 minutos consecutivos: esto es hipotensión "
         "sostenida por la obstrucción."),
        ("The systolic pressure has stayed below 90 mmHg for 15 minutes: this is sustained hypotension from the "
         "obstruction.",
         "La presión sistólica se ha mantenido bajo 90 mmHg por 15 minutos: esto es hipotensión sostenida por la "
         "obstrucción.")):
        assert language.say(english, "es") == spanish


def test_the_line_after_an_order_uses_the_room_s_approved_words():
    said = language.say("After heparin 5000 units IV administered, BP 109/70 mmHg · HR 124/min · SpO₂ 95% · RR "
                        "30/min. Alert; respiratory effort increased; capillary refill 3.1 s.", "es")
    assert "esfuerzo respiratorio aumentado;" in said  # OBSERVED_VALUES_ES: «Aumentado»
    assert language.say("albuterol 5 mg nebulized", "es") == "salbutamol 5 mg nebulizado"
    assert language.say("Glucose 25 g IV (50% × 50 mL)", "es") == "Glucosa 25 g IV (50% × 50 mL)"
    assert language.say("NIV start: BiPAP, FiO₂ 50%", "es").startswith("VMNI ")
    assert language.say("respiratory effort increased", "en") == "respiratory effort increased"
    record = {"agent": "albuterol", "dose_mg": 5, "route": "nebulized", "time_min": 16}
    assert family_reports.format_administration(record, "es") == "salbutamol 5 mg nebulizado · minuto 16"
    assert family_reports.format_administration(record) == "albuterol 5 mg nebulized · minute 16"


def test_the_room_writes_every_examination_entry_and_the_state_summary_in_spanish(monkeypatch):
    from test_curriculum_trajectories import load_engine
    engine = load_engine()
    monkeypatch.setattr(language, "current", lambda: "es")
    assert engine["_room_you_words"]("Examine: Abdomen") == "Examen: Abdomen"
    assert engine["_room_you_words"]("Examine: Cardiac") == "Examen: Cardíaco"
    assert engine["_room_you_words"]("Pain since this morning") == "Pain since this morning"
    snapshot = {"observable": {"spo2": 96}, "treatments": {"norepinephrine": True, "norepinephrine_rate": 0.05,
                                                           "nitroglycerin": True, "nitroglycerin_rate_mcg_min": 20}}
    summary = engine["_trace_state_words"](snapshot, "es")
    assert "Noradrenalina 0.05 mcg/kg/min en curso" in summary and "Nitroglicerina 20 mcg/min en curso" in summary
    assert "Norepinephrine" not in summary and "Nitroglycerin" not in summary
