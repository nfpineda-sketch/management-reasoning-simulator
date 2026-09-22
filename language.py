"""The language the encounter is presented in, kept apart from the one it is written in.

Faculty decision 16 of 2026-09-21, from the full bank review. A resident writes
in Spanish and the patient, the history, the results and the review all answered
in English, including sentences that mixed the two: "Your recorded expected
effect was: suba la frecuencia."

The decision separates three things, and this module owns the second:

  * **the language of input**, which is already both: an order in Spanish and the
    same order in English produce the same action, and nothing here changes that;
  * **the language of presentation**, which is a setting. Writing an order in
    Spanish must not change it; only the reader changes it, and changing it
    re-presents the same stored encounter rather than regenerating anything;
  * **the resident's own words**, which are kept verbatim and are never silently
    spliced into a sentence in the other language.

The record is stored in English, which is the engine's canonical form, and
translated where it is displayed. So the clinical identifiers, the numbers, the
doses, the units and the drug names are the same in both languages, and a
language change cannot alter physiology, timing or assessment.

This is the first stage the decision asked for: the fixed text — labels, states
and system messages. The authored narrative of each case (presentation, history
answers, examination prose) is still English and is the next stage.
"""
import os
import re

LANGUAGES = {"en": "English", "es": "Español"}
DEFAULT = "en"          # the UH environment keeps English as its default


def configured():
    """The language from the environment, for a headless run."""
    choice = str(os.environ.get("MRS_LANGUAGE", "") or "").strip().lower()
    return choice if choice in LANGUAGES else DEFAULT


def current():
    """The language this session is presenting in."""
    try:
        import streamlit as st
        value = st.session_state.get("presentation_language")
        if value in LANGUAGES:
            return value
    except Exception:
        pass
    return configured()


# Whole messages, where a sentence has to be said rather than substituted.
MESSAGES = {
 "The blocker is still working and the hypnotic is not: the patient cannot move and is not sedated. Nothing on the monitor will say so.":
 "El bloqueador sigue actuando y el hipnótico no: el paciente no puede moverse y no está sedado. Nada en el monitor lo va a decir.",
 "Complete atrioventricular block: the inferior infarct has taken the AV node. The rate falls and the pressure falls with it.":
 "Bloqueo auriculoventricular completo: el infarto inferior tomó el nodo AV. La frecuencia cae y la presión cae con ella.",
 "Acute withdrawal: the patient is agitated, retching and sweating, with a rising pressure and rate. The target of the antidote is ventilation, not consciousness.":
 "Abstinencia aguda: el paciente está agitado, con arcadas y sudoroso, con la presión y la frecuencia en alza. El objetivo del antídoto es la ventilación, no la conciencia.",
 "The patient retches and vomits shortly after the morphine. It is the drug's own effect, not a new ischaemic symptom, and anything given by mouth is now of uncertain absorption.":
 "El paciente presenta arcadas y vomita poco después de la morfina. Es un efecto del fármaco, no un síntoma isquémico nuevo, y lo dado por boca queda de absorción incierta.",
 "The patient passes urine. Nobody is collecting it, so the volume is not quantified.":
 "El paciente orina. Nadie lo está recolectando, así que el volumen no queda cuantificado.",
 "Cardiovascular collapse is a terminal state in this build. Ordinary reassessment is paused; arrest-management actions are not yet executable.":
 "El colapso cardiovascular es un estado terminal en esta versión. La reevaluación ordinaria queda en pausa; las acciones de manejo del paro todavía no son ejecutables.",
 "I preserved your input, but this build does not yet execute that action.":
 "Conservé lo que escribiste, pero esta versión todavía no ejecuta esa acción.",
 "This intervention requires a generated encounter with an explicit response rule.":
 "Esta intervención requiere un encuentro generado con una regla de respuesta explícita.",
 "Specify one supported study per order.": "Indica un solo examen soportado por orden.",
 "The requested study was not recognized.": "El examen solicitado no se reconoció.",
 "Specify which recorded drug or fluid to repeat.":
 "Indica cuál de los fármacos o fluidos registrados se repite.",
 "Which crystalloid would you like to give (for example, normal saline or LR)?":
 "¿Qué cristaloide quieres pasar (por ejemplo, suero fisiológico o Ringer lactato)?",
 "A crystalloid bolus is given IV or IO. Please specify the route.":
 "Un bolo de cristaloide se pasa IV o IO. Indica la vía.",
 "Where would you like to transfer or admit the patient?":
 "¿A dónde quieres trasladar u hospitalizar al paciente?",
 "Specify where the patient is admitted or transferred: the ICU, the coronary care unit, intermediate care, the ward, or home.":
 "Indica a dónde se hospitaliza o traslada: UCI, unidad coronaria, intermedio, sala o domicilio.",
 "Which specialist or reperfusion service would you like to contact?":
 "¿A qué especialista o servicio de reperfusión quieres contactar?",
 "No active ventilator or NIV settings are recorded. Specify the support to start.":
 "No hay parámetros de ventilador ni de VMNI registrados. Indica qué soporte iniciar.",
 "Specify the ventilator mode, FiO₂ as a percentage and PEEP in cm H₂O.":
 "Indica el modo del ventilador, la FiO₂ en porcentaje y la PEEP en cm H₂O.",
 "Specify the pacing rate in beats per minute and the output current in mA.":
 "Indica la frecuencia del marcapasos en latidos por minuto y la corriente en mA.",
 "Specify the neuromuscular blocker dose, in mg or mg/kg.":
 "Indica la dosis del bloqueador neuromuscular, en mg o mg/kg.",
 "A neuromuscular blocker is given IV or IO, not by that route.":
 "Un bloqueador neuromuscular se administra IV o IO, no por esa vía.",
 "Specify the infusion rate and its units (for example, propofol 2 mg/kg/h).":
 "Indica la velocidad de infusión y sus unidades (por ejemplo, propofol 2 mg/kg/h).",
 "Specify a supported fixed dose and route; this medication order uses weight or infusion-rate units.":
 "Indica una dosis fija y una vía soportadas; esta orden usa unidades de peso o de velocidad de infusión.",
 "This fixed-dose medication order needs an explicit new dose; stopping it is not a supported new administration.":
 "Esta orden de dosis fija necesita una dosis nueva explícita; suspenderla no es una administración nueva.",
 "Separate each medication or fluid with its own dose and route so the order is unambiguous.":
 "Separa cada fármaco o fluido con su propia dosis y vía para que la orden no sea ambigua.",
 "Separate each medication with its own dose and route so the order is unambiguous.":
 "Separa cada fármaco con su propia dosis y vía para que la orden no sea ambigua.",
 "Specify the medication dose in mass units (mg or g), not units.":
 "Indica la dosis en unidades de masa (mg o g), no en unidades.",
 "Specify one delivery duration for each treatment.":
 "Indica una sola duración de administración por tratamiento.",
 "Specify the reassessment interval in minutes.": "Indica el intervalo de reevaluación en minutos.",
 "An oxygen saturation target is not a device or flow order. Specify the oxygen device and flow to administer.":
 "Una meta de saturación no es una orden de dispositivo ni de flujo. Indica el dispositivo de oxígeno y el flujo.",
 "The patient is not fully alert. Please clarify the intended route and airway protection before oral glucose.":
 "El paciente no está plenamente alerta. Aclara la vía y la protección de la vía aérea antes de dar glucosa oral.",
 "The patient is receiving invasive ventilation. Please specify ventilator settings or clarify the intended airway change.":
 "El paciente está en ventilación invasiva. Indica parámetros del ventilador o aclara el cambio de vía aérea.",
 "Name one supported order to replace that item, or say cancel. Every other order in the same submission is still held.":
 "Nombra una orden soportada que reemplace ese ítem, o di cancelar. El resto de la misma orden sigue retenido.",
 "Specify one replacement study, or say cancel study. The other orders remain pending.":
 "Indica un examen de reemplazo, o di cancelar examen. Las demás órdenes siguen pendientes.",
 "AI analysis is not configured for this application. You can still review and download your original encounter record.":
 "El análisis con IA no está configurado en esta aplicación. Puedes revisar y descargar tu registro original del encuentro.",
}

# Ordered substitutions: the composable fragments the engine assembles its
# sentences from. Longest and most specific first; anything with no rule stays
# in English rather than breaking.
_RULES = (
 # --- response card scaffolding -------------------------------------------
 (r"\bAfter (\d+) minutes,", r"Tras \1 minutos,"),
 (r"\bAfter ", "Tras "),
 (r"\bThe patient reports no pain\b", "El paciente no refiere dolor"),
 (r"\bThe patient reports severe pain\b", "El paciente refiere dolor intenso"),
 (r"\bThe patient reports moderate pain\b", "El paciente refiere dolor moderado"),
 (r"\bThe patient reports mild pain\b", "El paciente refiere dolor leve"),
 # --- vital signs ----------------------------------------------------------
 (r"\bBP (\d+)/(\d+) mmHg", r"PA \1/\2 mmHg"),
 (r"\bHR (\d+)/min", r"FC \1/min"),
 (r"\bSpO₂ (\d+)%", r"SpO₂ \1%"),
 (r"\bRR (\d+)/min", r"FR \1/min"),
 (r"\bcapillary refill ([\d.]+) s", r"llene capilar \1 s"),
 (r"\brespiratory effort ", "esfuerzo respiratorio "),
 (r"\bRespiratory rate: (\d+)/min", r"Frecuencia respiratoria: \1/min"),
 (r"\bWork of breathing: ", "Trabajo respiratorio: "),
 (r"\bMental status: ", "Estado mental: "),
 (r"\bCurrent mental status: ", "Estado mental actual: "),
 # --- states ---------------------------------------------------------------
 (r"\bExhausted: shallow and ineffective effort\b", "Agotado: esfuerzo superficial e ineficaz"),
 (r"\bParalysed, sedation not maintained\b", "Paralizado, sin sedación mantenida"),
 (r"\bAwake and fighting the ventilator\b", "Despierto y luchando con el ventilador"),
 (r"\bVentilator-supported, no spontaneous effort\b", "Soportado por el ventilador, sin esfuerzo espontáneo"),
 (r"\bVentilator-supported\b", "Soportado por el ventilador"),
 (r"\bVentilator dyssynchrony\b", "Disincronía con el ventilador"),
 (r"\bmarkedly increased\b", "muy aumentado"), (r"\bMarkedly increased\b", "Muy aumentado"),
 (r"\bmoderately increased\b", "moderadamente aumentado"), (r"\bModerately increased\b", "Moderadamente aumentado"),
 (r"\bmildly increased\b", "levemente aumentado"), (r"\bMildly increased\b", "Levemente aumentado"),
 (r"\bUnresponsive\b", "Sin respuesta"), (r"\bunresponsive\b", "sin respuesta"),
 (r"\bObtunded\b", "Obnubilado"), (r"\bobtunded\b", "obnubilado"),
 (r"\bDrowsy\b", "Somnoliento"), (r"\bdrowsy\b", "somnoliento"),
 (r"\bConfused\b", "Confuso"), (r"\bconfused\b", "confuso"),
 (r"\bAgitated\b", "Agitado"), (r"\bagitated\b", "agitado"),
 (r"\bSedated\b", "Sedado"), (r"\bsedated\b", "sedado"),
 (r"\bAlert\b", "Alerta"), (r"\balert\b", "alerta"),
 (r"\bSevere\b", "Severo"), (r"\bsevere\b", "severo"),
 (r"\bReduced\b", "Reducido"), (r"\breduced\b", "reducido"),
 (r"\bAbsent\b", "Ausente"), (r"\babsent\b", "ausente"),
 (r"\bNormal\b", "Normal"), (r"\bnormal\b", "normal"),
 # --- rhythms --------------------------------------------------------------
 (r"\bSinus tachycardia\b", "Taquicardia sinusal"), (r"\bSinus bradycardia\b", "Bradicardia sinusal"),
 (r"\bSinus rhythm\b", "Ritmo sinusal"), (r"\bComplete AV block\b", "Bloqueo AV completo"),
 (r"\bPaced rhythm, capture confirmed\b", "Ritmo de marcapasos, captura confirmada"),
 (r"\bPacing spikes without capture, underlying complete AV block\b",
  "Espigas de marcapasos sin captura, sobre un bloqueo AV completo"),
 (r"\bAsystole\b", "Asistolía"),
 # --- orders and their labels ---------------------------------------------
 (r"\badministered\b", "administrado"),
 (r"\bstarted at\b", "iniciado a"), (r"\badjusted to\b", "ajustado a"),
 (r"\b(\w+) infusion stopped\b", r"infusión de \1 suspendida"),
 (r"\b(\w+) infusion\b", r"infusión de \1"),
 (r"\bstart\b", "inicio"), (r"\bstop\b", "suspensión"), (r"\badjust\b", "ajuste"),
 (r"\bNasal cannula\b", "Naricera"), (r"\bnasal cannula\b", "naricera"),
 (r"\bNon-rebreather mask\b", "Mascarilla con reservorio"), (r"\bnon-rebreather mask\b", "mascarilla con reservorio"),
 (r"\bSimple mask\b", "Mascarilla simple"), (r"\bsimple mask\b", "mascarilla simple"),
 (r"\bRoom air\b", "Aire ambiente"), (r"\broom air\b", "aire ambiente"),
 (r"\bBag-mask ventilation\b", "Ventilación con bolsa-mascarilla"),
 (r"\bInvasive ventilation\b", "Ventilación invasiva"),
 (r"\bat (\d+(?:\.\d+)?) L/min", r"a \1 L/min"),
 (r"\bPacked red cells\b", "Glóbulos rojos"),
 (r"\bnormal saline\b", "suero fisiológico"), (r"\bNormal saline\b", "Suero fisiológico"),
 (r"\blactated Ringer's\b", "Ringer lactato"),
 (r"\bstarted over (\d+) min\b", r"a pasar en \1 min"),
 (r"\bTransfer/admission requested: ", "Traslado u hospitalización solicitada: "),
 (r"\bDischarge home requested\b", "Alta a domicilio indicada"),
 (r"\bcath lab activated\b", "hemodinamia activada"),
 (r"\bcath lab contacted for angiography\b", "hemodinamia contactada para coronariografía"),
 (r"\bcath lab contacted\b", "hemodinamia contactada"),
 (r"\bcontacting ([a-z ]+) \(no intervention yet\)", r"contactando a \1 (sin intervención aún)"),
 # --- held orders ----------------------------------------------------------
 (r"\*\*ORDER HELD — CLARIFICATION REQUIRED\*\*", "**ORDEN RETENIDA — SE NECESITA UNA ACLARACIÓN**"),
 (r"\*\*ORDER HELD — REASONING REQUIRED\*\*", "**ORDEN RETENIDA — FALTA EL RAZONAMIENTO**"),
 (r"\bI understood:", "Entendí:"),
 (r"Nothing in this order was executed and the patient state has not changed\.",
  "No se ejecutó nada de esta orden y el estado del paciente no ha cambiado."),
 (r"The order has not been executed and the patient state has not changed\.",
  "La orden no se ejecutó y el estado del paciente no ha cambiado."),
 (r"The other orders in this submission are held until then\.",
  "Las demás órdenes de esta entrega quedan retenidas hasta entonces."),
 (r"Replace it with a supported intervention, dose/settings and route, or say cancel\.",
  "Reemplázala por una intervención soportada, con dosis o parámetros y vía, o di cancelar."),
 (r"This order was not recognized:", "Esta orden no se reconoció:"),
 (r"The held order was discarded to run this one:", "La orden retenida se descartó para ejecutar esta:"),
 (r"None of it was administered\.", "No se administró nada de ella."),
 (r"Before execution, please add:", "Antes de ejecutarla, agrega:"),
 (r"Use your own words, or complete the guided sentence starters on screen\.",
  "Usa tus propias palabras, o completa los inicios de frase en pantalla."),
 (r"You do not need to repeat the order\.", "No necesitas repetir la orden."),
 # --- investigations -------------------------------------------------------
 (r"\bPerformed at minute (\d+)", r"Realizado en el minuto \1"),
 (r"\bSample obtained at minute (\d+)", r"Muestra tomada en el minuto \1"),
 (r"\bMeasured at minute (\d+)", r"Medido en el minuto \1"),
 (r"\b12-lead tracing available in ECG recordings at the bedside\.",
  "Trazado de 12 derivaciones disponible en los registros de ECG."),
 (r"\bBedside glucose\b", "Glicemia capilar"), (r"\bLaboratory results\b", "Resultados de laboratorio"),
 (r"\bChest X-ray\b", "Radiografía de tórax"), (r"\bBlood cultures\b", "Hemocultivos"),
 (r"\bArterial blood gas\b", "Gases arteriales"), (r"\bVenous blood gas\b", "Gases venosos"),
 (r"\bTroponin\b", "Troponina"), (r"\bLactate\b", "Lactato"), (r"\bHemoglobin\b", "Hemoglobina"),
 (r"\bTemperature\b", "Temperatura"), (r"\bUrinalysis\b", "Orina completa"),
 (r"\bCT pulmonary angiography\b", "AngioTAC de tórax"),
 (r"\bRight-sided ECG \(V3R-V4R\)", "ECG con derivadas derechas (V3R-V4R)"),
 (r"\bPosterior ECG \(V7-V9\)", "ECG con derivaciones posteriores (V7-V9)"),
 (r"\bGlucose (\d+) mg/dL", r"Glucosa \1 mg/dL"),
 (r"\bUpper reference\b", "Referencia superior"),
 # --- the monitor's own labels ---------------------------------------------
 (r"^SIM TIME$", "TIEMPO SIM"), (r"^BP · MAP$", "PA · PAM"), (r"^HR$", "FC"),
 (r"^SpO₂ · SUPPORT$", "SpO₂ · SOPORTE"),
 (r"^RR · WORK OF BREATHING$", "FR · TRABAJO RESPIRATORIO"),
 (r"^CRT · EXTREMITIES$", "LLENE · EXTREMIDADES"), (r"^MENTAL STATUS$", "ESTADO MENTAL"),
 (r"^Not measured$", "No medido"), (r"^Not measurable$", "No medible"),
 (r"^No measurable BP$", "Sin PA medible"), (r"^No reliable reading$", "Sin lectura confiable"),
 (r"\bPATIENT RESPONSE\b", "RESPUESTA DEL PACIENTE"),
 (r"\bINITIAL PRESENTATION\b", "PRESENTACIÓN INICIAL"),
 (r"\bPATIENT HISTORY\b", "ANAMNESIS"), (r"\bEXAMINATION\b", "EXAMEN FÍSICO"),
 (r"\bCLINICAL UPDATE\b", "ACTUALIZACIÓN CLÍNICA"), (r"\bCLARIFICATION\b", "ACLARACIÓN"),
 (r"\bDIAGNOSTIC RESULTS\b", "RESULTADOS DE EXÁMENES"), (r"\bPROCEDURE\b", "PROCEDIMIENTO"),
 (r"\bREASONING COMPLETION\b", "COMPLETAR EL RAZONAMIENTO"),
 (r"\bCONTEXT CHECK — DOES NOT BLOCK EXECUTION\b", "REVISIÓN DE CONTEXTO — NO BLOQUEA LA EJECUCIÓN"),
 (r"^YOU$", "TÚ"), (r"^PROTOTYPE$", "PROTOTIPO"),
 # --- the bedside panel and the page's own chrome ---------------------------
 (r"^BP: no measurable blood pressure$", "PA: sin presión medible"),
 (r"^BP: (\d+)/(\d+) mmHg$", r"PA: \1/\2 mmHg"),
 (r"^HR: (\d+)/min$", r"FC: \1/min"),
 (r"^SpO₂: (\d+)%$", r"SpO₂: \1%"),
 (r"^SpO₂: no reliable reading$", "SpO₂: sin lectura confiable"),
 (r"^CRT: ([\d.]+) s$", r"Llene capilar: \1 s"),
 (r"^CRT: not measurable$", "Llene capilar: no medible"),
 (r"Monitor: organized electrical activity at (\d+)/min, no palpable pulse",
  r"Monitor: actividad eléctrica organizada a \1/min, sin pulso palpable"),
 (r"^### Management$", "### Manejo"), (r"^### Orders$", "### Exámenes"),
 (r"#### Arrival & handover", "#### Llegada y entrega"),
 (r"No investigation reports have been received yet\.", "Todavía no hay informes de exámenes."),
 (r"\bpending · expected at (\d+) min", r"pendiente · esperado a los \1 min"),
 # --- pathway messages -----------------------------------------------------
 (r"Cath lab activated in this centre: the artery is expected to be open at minute (\d+) \(door to balloon (\d+) minutes\)\.",
  r"Hemodinamia activada en este centro: se espera la arteria abierta en el minuto \1 (puerta-balón \2 minutos)."),
 (r"Cath lab contacted in this centre: angiography is scheduled for minute (\d+)\.",
  r"Hemodinamia contactada en este centro: la coronariografía queda programada para el minuto \1."),
 (r"This pattern demands angiography and rules out provocation testing, even though the patient is pain-free\.",
  "Este patrón obliga a coronariografía y descarta las pruebas de provocación, aunque el paciente esté sin dolor."),
 (r"Cath lab contacted\. This ECG shows no occlusion pattern: immediate angiography is not required, and the pathway here is antiplatelet and anticoagulant treatment with a monitored bed and reassessment\.",
  "Hemodinamia contactada. Este ECG no muestra patrón de oclusión: no se requiere coronariografía inmediata, y el camino aquí es antiagregación y anticoagulación con cama monitorizada y reevaluación."),
 (r"The artery is open after percutaneous coronary intervention: the ST segment resolves on a repeated ECG and the discomfort settles\. The troponin climbs faster now, from washout, which is not a failed procedure; its peak comes hours later\. The affected wall recovers only partly\.",
  "La arteria está abierta tras la angioplastia: el segmento ST se resuelve en un ECG repetido y el dolor cede. La troponina sube más rápido ahora, por lavado, lo que no es un procedimiento fallido; su peak llega horas después. La pared afectada se recupera solo en parte."),
 (r"Gastroenterology performed upper endoscopy: bleeding ulcer treated endoscopically; active bleeding controlled\. Rebleeding remains possible\.",
  "Gastroenterología realizó la endoscopía alta: úlcera sangrante tratada endoscópicamente; sangrado activo controlado. El resangrado sigue siendo posible."),
 (r"Systemic thrombolysis given for sustained hypotension: the obstruction begins to fall within minutes and keeps falling for about half an hour\.",
  "Trombolisis sistémica por hipotensión sostenida: la obstrucción empieza a ceder en minutos y sigue cediendo por media hora."),
 (r"The systolic pressure has stayed below 90 mmHg for 15 minutes: this is sustained hypotension from the obstruction\.",
  "La presión sistólica se ha mantenido bajo 90 mmHg por 15 minutos: esto es hipotensión sostenida por la obstrucción."),
 (r"The patient was brought back to the emergency department after being sent home: ",
  "El paciente volvió al servicio de urgencia después de ser enviado a casa: "),
 (r"The problem that sent them home had not finished\.", "El problema que lo mandó a casa no había terminado."),
 (r"found ([\w ]+) at home", r"encontrado \1 en su casa"),
 (r"Intubation was performed while the patient was still alert, oxygenating and responding to treatment: spontaneous ventilation is lost and the airway pressures now govern the circulation\.",
  "Se intubó a un paciente que seguía alerta, oxigenando y respondiendo al tratamiento: se pierde la ventilación espontánea y las presiones de la vía aérea pasan a gobernar la circulación."),
 (r"Intubation was performed while the patient was failing but still perfusing\.",
  "Se intubó a un paciente que estaba claudicando pero todavía perfundía."),
 (r"Dobutamine at ([\d.]+) mcg/kg/min: the rate climbs and frequent ventricular ectopy appears on the monitor\. The inotrope is buying contraction with myocardial oxygen demand\.",
  r"Dobutamina a \1 mcg/kg/min: la frecuencia sube y aparece ectopia ventricular frecuente en el monitor. El inótropo está comprando contracción con demanda miocárdica de oxígeno."),
 (r"Cardiac arrest after (\d+) minutes of paralysis without ventilation\. The blocker removed every breath the patient had; the ventilation that replaces them was never established\.",
  r"Paro cardíaco tras \1 minutos de parálisis sin ventilación. El bloqueador quitó todas las respiraciones del paciente; la ventilación que las reemplaza nunca se estableció."),
 (r"Respiratory arrest after twenty minutes of unsupported apnoeic breathing, and the circulation follows it\. Ventilation was the treatment that was missing, with or without the antidote\.",
  "Paro respiratorio tras veinte minutos de respiración apneica sin soporte, y la circulación lo sigue. La ventilación era el tratamiento que faltaba, con o sin antídoto."),
 (r"Confusion persists with nystagmus and an unsteady gaze although the glucose is now normal: glucose was given to a thiamine-depleted brain\. Thiamine is the missing treatment\.",
  "La confusión persiste con nistagmo y mirada inestable aunque la glicemia ya es normal: se dio glucosa a un cerebro depletado de tiamina. La tiamina es el tratamiento que falta."),
 (r"Generalized tonic-clonic seizure after twenty minutes below 40 mg/dL\. It stops on its own and leaves the patient post-ictal; the treatment is the glucose, not an anticonvulsant\.",
  "Convulsión tónico-clónica generalizada tras veinte minutos bajo 40 mg/dL. Cede sola y deja al paciente en estado postictal; el tratamiento es la glucosa, no un anticonvulsivante."),

 # --- more system messages, templated --------------------------------------
 (r"Please specify a supported route for ([\w-]+)\.", r"Indica una vía soportada para \1."),
 (r"Please specify or confirm the ([\w_]+) dose in milligrams\.",
  r"Indica o confirma la dosis de \1 en miligramos."),
 (r"Specify the dose, the dose units and the route\.", "Indica la dosis, sus unidades y la vía."),
 (r"\bSpecify the ", "Indica "), (r"\bSpecify an? ", "Indica "), (r"\bSpecify one ", "Indica un solo "),
 (r"Requested study '([\w_]+)' is unavailable\.", r"El examen solicitado '\1' no está disponible."),
 (r"Available studies:", "Exámenes disponibles:"),
 (r"No orders in this submission were executed\.", "No se ejecutó ninguna orden de esta entrega."),
 (r"Choose a reassessment within this case's supported time horizon\.",
  "Elige una reevaluación dentro del horizonte de tiempo del caso."),
 (r"Indica a reassessment interval from (\d+) to (\d+) minutes\.",
  r"Indica un intervalo de reevaluación entre \1 y \2 minutos."),
 # --- pacing, blockade and support labels ----------------------------------
 (r"transcutaneous pacing at ([\d.]+)/min and ([\d.]+) mA", r"marcapasos transcutáneo a \1/min y \2 mA"),
 (r"Pacing spikes are followed by wide complexes and a palpable pulse: capture is confirmed\.",
  "Las espigas son seguidas de complejos anchos y pulso palpable: hay captura."),
 (r"Pacing spikes appear without a following complex: there is no capture at this output\.",
  "Aparecen espigas sin complejo que las siga: no hay captura con esta corriente."),
 (r"Intravenous orders were already being given through a working line\.",
  "Las órdenes endovenosas ya se estaban pasando por una vía permeable."),
 (r"The monitor watches the patient and treats nothing\.", "El monitor vigila al paciente y no trata nada."),
 (r"Nothing is to be given by mouth\.", "Nada por boca."),
 (r"Urine is collected and measured from now on; the catheter does not make any\.",
  "Desde ahora la orina se recolecta y se mide; la sonda no produce ninguna."),
 (r"What it is for belongs to the indication\.", "Para qué es, depende de la indicación."),
 (r"([\d.]+) mL drained on placement, made before the catheter went in\.",
  r"\1 mL drenados al instalarla, producidos antes de que la sonda entrara."),
 (r"\bperipheral intravenous access placed\b", "acceso venoso periférico instalado"),
 (r"\bcontinuous monitoring and pulse oximetry started\b", "monitorización continua y oximetría de pulso iniciadas"),
 (r"\bnil by mouth recorded\b", "régimen cero registrado"),
 (r"\burinary catheter placed\b", "sonda vesical instalada"),
 (r"\bnasogastric tube placed\b", "sonda nasogástrica instalada"),
 (r"transcutaneous pacing stopped", "marcapasos transcutáneo suspendido"),
 (r"movement is abolished for about (\d+) minutes\. It does not sedate and it does not relieve pain\.",
  r"el movimiento queda abolido por unos \1 minutos. No seda y no quita el dolor."),
 (r"atropine withheld: ([\d.]+) mg has already been given and ([\d.]+) mg is the maximum; this block needs pacing, not more atropine",
  r"atropina no administrada: ya se dieron \1 mg y el máximo es \2 mg; este bloqueo necesita marcapasos, no más atropina"),
 (r"peripheral intravenous access already in place; not repeated", "acceso venoso periférico ya instalado; no se repite"),
 (r"peripheral intravenous access: .*?one\b", "acceso venoso periférico instalado"),
 (r"continuous monitoring and pulse oximetry: the monitor is on; it watches the patient and treats nothing",
  "monitorización continua y oximetría de pulso: el monitor está puesto; vigila al paciente y no trata nada"),
 (r"urinary catheter: urine is now collected and measured; the catheter does not make any",
  "sonda vesical: la orina queda recolectada y medida; la sonda no produce ninguna"),
 (r"nil by mouth: recorded; nothing is to be given by mouth", "régimen cero: registrado; nada por boca"),
 (r"nasogastric tube: placed; what it is for belongs to the indication",
  "sonda nasogástrica: instalada; para qué es, depende de la indicación"),
 (r"([\w ]+) already in place; not repeated", r"\1 ya instalado; no se repite"),
 (r"(\d+) mL of urine collected between minute (\d+) and minute (\d+) \(about (\d+) mL/h\)\.",
  r"Se recolectaron \1 mL de orina entre el minuto \2 y el minuto \3 (unos \4 mL/h)."),
 (r"([\w-]+) withheld by mouth: the patient is ([\w ]+) and swallowing is not safe",
  r"\1 no administrado por boca: el paciente está \2 y la deglución no es segura"),
 (r"([\w-]+) on top of ([\w-]+): two NSAIDs are one class\. The second adds the risks and very little of the effect\.",
  r"\1 sobre \2: dos AINE son una sola clase. El segundo suma los riesgos y muy poco del efecto."),
 (r"(\w+) already given at minute (\d+); not repeated", r"\1 ya administrado en el minuto \2; no se repite"),
)
_COMPILED = tuple((re.compile(pattern), replacement) for pattern, replacement in _RULES)


def say(text, language=None):
    """Present a stored English string in the reading language."""
    language = language or current()
    if language == "en" or not text:
        return text
    body = str(text)
    exact = MESSAGES.get(body.strip())
    if exact:
        return exact
    for sentence, translation in MESSAGES.items():
        if sentence in body:
            body = body.replace(sentence, translation)
    for pattern, replacement in _COMPILED:
        body = pattern.sub(replacement, body)
    return body
