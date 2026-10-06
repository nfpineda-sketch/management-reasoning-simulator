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

This was the first stage the decision asked for: the fixed text — labels, states
and system messages. The authored narrative of each bank case (presentation,
history answers, examination and study-report prose) followed on 2026-09-26 as
whole passages the faculty approved case by case (``narrative``, ``case_text``).
"""
from contextlib import contextmanager
from contextvars import ContextVar
import os
import re

LANGUAGES = {"en": "English", "es": "Español"}
DEFAULT = "en"          # the UH environment keeps English as its default

#: The language of the document being written right now, when it is not the
#: session's: a document follows the language its encounter was played in, or
#: the one its reader chose, while the app around it keeps the reader's own
#: (faculty, 2026-09-26). Set only inside ``presenting``.
_DOCUMENT = ContextVar("document_language", default=None)


def configured():
    """The language from the environment, for a headless run."""
    choice = str(os.environ.get("MRS_LANGUAGE", "") or "").strip().lower()
    return choice if choice in LANGUAGES else DEFAULT


@contextmanager
def presenting(code):
    """Write what happens inside this block in ``code``, whatever the session shows.

    An unknown or empty code changes nothing: the session's language stands.
    """
    token = _DOCUMENT.set(code if code in LANGUAGES else None)
    try:
        yield
    finally:
        _DOCUMENT.reset(token)


def current():
    """The language this session is presenting in, or the document being written."""
    document = _DOCUMENT.get()
    if document in LANGUAGES:
        return document
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
 # The standing line, said whole so the Spanish agrees with its noun (2026-09-26).
 "I couldn't match that question to the recorded history. Please rephrase it or use History topics.":
 "No pude relacionar esa pregunta con la historia registrada. Reformúlala o usa los temas de la anamnesis.",
 "Peripheral intravenous access already in place; not repeated":
 "Vía venosa periférica ya instalada; no se repite",
 # A pregnancy or last-period question on a case that documents none (DF-23 row 8).
 "Not documented.":
 "No documentado.",
 # The engine's question when the units were not written, or two counts were (TD-26).
 "Confirm the number of packed red-cell units (1–4 per order).":
 "Confirma el número de unidades de glóbulos rojos (1 a 4 por orden).",
 'You have not recorded a destination. Do you want to continue or finish?':
 'No has registrado un destino. ¿Quieres continuar o finalizar?',
 'How is this encounter ending?':
 '¿Cómo termina este encuentro?',
 'Clinical close: my management is complete':
 'Cierre clínico: mi manejo está completo',
 'Interruption: I have to stop here':
 'Interrupción: tengo que detenerme aquí',
 'Early finish: I am ending before its natural end':
 'Finalización anticipada: termino antes de su final natural',
 'Continue the encounter':
 'Continuar el encuentro',
 'Finish now':
 'Finalizar ahora',
 # The room's notices after an urgent order and a facilitator's override (TD-23, cycle 8).
 "Facilitator override accepted. The held order was executed with incomplete prospective reasoning.":
 "Anulación docente aceptada. La orden retenida se ejecutó con el razonamiento prospectivo incompleto.",
 "Facilitator override accepted, but the order did not run: see the message below.":
 "Anulación docente aceptada, pero la orden no se ejecutó: mira el mensaje de abajo.",
 # The engine's answer to a delivery time it cannot run (cycle 8).
 "Specify a positive supported delivery duration for a fluid, blood or fixed-dose medication.":
 "Indica un tiempo de administración válido para el fluido, la sangre o el medicamento de dosis fija.",
 'What do you think is going on?':
 '¿Qué crees que está pasando?',
 'What are you going to do?':
 '¿Qué vas a hacer?',
 'What do you expect to happen, or what are you trying to clarify?':
 '¿Qué esperas que ocurra o qué buscas aclarar?',
 'What will you check, and when?':
 '¿Qué vas a revisar y cuándo?',
 'What will you check?':
 '¿Qué vas a revisar?',
 'Which problem are you addressing first? (optional)':
 '¿Qué problema estás abordando primero? (opcional)',
 'Your current explanation of the problem and the findings that support it. You do not need a definitive diagnosis.':
 'Tu explicación actual del problema y los hallazgos que la apoyan. No necesitas un diagnóstico definitivo.',
 'The interventions, studies or measures you want to order.':
 'Las intervenciones, estudios o medidas que quieres indicar.',
 'The response you anticipate, or the information you expect to obtain to guide management.':
 'La respuesta que anticipas o la información que esperas obtener para orientar el manejo.',
 'The variables or findings you will check, and the moment or condition for doing so.':
 'Las variables o hallazgos que comprobarás y el momento o condición para hacerlo.',
 'This is what the engine understood. To change it, cancel and write the order again below.':
 'Esto es lo que entendió el motor. Para cambiarlo, cancela y escribe la orden de nuevo abajo.',
 'I will check in… minutes':
 'Voy a revisar en… minutos',
 '#### Answer what is missing':
 '#### Responde lo que falta',
 'Write what you are doing in your own words: what you think is going on, what you are going to do, what you expect, and what you will check.':
 'Escribe lo que estás haciendo con tus propias palabras: qué crees que está pasando, qué vas a hacer, qué esperas y qué vas a revisar.',
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
 # A bleeding measure named by none (C7-06, 2026-09-28).
 "Specify a tourniquet, direct pressure or wound packing.":
     "Indica cuál medida: torniquete, compresión directa o taponamiento de la herida.",
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

# One observed value as the record stores it ("Increased", "Warm"), for a document
# or a table that prints it on its own. Exact matches only: a bare word must
# never be replaced inside a longer sentence (faculty, 2026-09-26).
OBSERVED_VALUES_ES = {
    "Alert": "Alerta", "Drowsy": "Somnoliento", "Obtunded": "Obnubilado", "Unresponsive": "Sin respuesta",
    "Confused": "Confuso", "Agitated": "Agitado", "Sedated": "Sedado",
    "Sedated after intubation": "Sedado tras la intubación", "Normal": "Normal",
    "Increased": "Aumentado", "Mildly increased": "Levemente aumentado", "Markedly increased": "Muy aumentado",
    "Severe": "Severo", "Ventilator-supported": "Con soporte ventilatorio", "Reduced": "Reducido",
    "Absent": "Ausente", "Warm": "Tibias", "Cool": "Frías", "Cold": "Heladas", "Very cold": "Muy frías",
    "Mottled": "Moteadas", "Mottled/cold": "Moteadas/heladas", "Yes": "Sí", "No": "No",
    # The rhythms the engine names by their English initials, by their Spanish ones.
    "AF": "FA", "VT": "TV", "VF": "FV", "PEA": "AESP",
}
#: The same values whatever their case: the trace keeps some lowercased ("cool").
_OBSERVED_FOLDED = {key.lower(): value for key, value in OBSERVED_VALUES_ES.items()}


def observed_value(text, language=None):
    """One stored observation value in the reading language; anything else as ``say`` says it.

    A value stored in lower case ("cool") is said in lower case ("frías"); an
    acronym keeps its capitals.
    """
    language = language or current()
    if language == "en" or not text:
        return text
    stripped = str(text).strip()
    exact = OBSERVED_VALUES_ES.get(stripped)
    if exact:
        return exact
    folded = _OBSERVED_FOLDED.get(stripped.lower())
    if folded:
        return folded.lower() if stripped == stripped.lower() and not folded.isupper() else folded
    return say(text, language)


# Ordered substitutions: the composable fragments the engine assembles its
# sentences from. Longest and most specific first; anything with no rule stays
# in English rather than breaking.
# The services a consult names, as a Spanish sentence names them. The cath lab
# has its own sentences below.
_SERVICES_ES = {"PERT": "el equipo PERT", "cardiology": "cardiología", "gastroenterology": "gastroenterología",
                "urology": "urología", "surgery": "cirugía general", "ICU": "la UCI",
                "endocrinology": "endocrinología", "nephrology": "nefrología", "neurology": "neurología",
                "internal medicine": "medicina interna", "toxicology": "toxicología"}


#: Where a patient is admitted, as a Spanish sentence names it (the engine's destinations).
_DESTINATIONS_ES = {"ICU": "UCI", "ward": "sala", "intermediate care": "intermedio", "coronary care unit": "unidad coronaria",
                    "coronary care": "unidad coronaria", "operating room": "pabellón", "theatre": "pabellón",
                    "cath lab": "hemodinamia", "stroke unit": "unidad de ACV", "step-down unit": "intermedio"}
#: How an external bleed is controlled, and the words a site is written with.
_HAEMOSTASIS_ES = {"Tourniquet": "Torniquete aplicado", "Direct pressure": "Compresión directa aplicada",
                   "Pressure": "Compresión aplicada", "Packing": "Taponamiento aplicado",
                   "Wound packing": "Taponamiento de la herida aplicado", "Pressure dressing": "Vendaje compresivo aplicado",
                   "Hemostatic dressing": "Apósito hemostático aplicado"}
_IO_SITES_ES = {"humeral": "humeral", "tibial": "tibial", "sternal": "esternal", "femoral": "femoral"}
_SITE_WORDS_ES = {"left": "izquierdo", "right": "derecho", "thigh": "muslo", "leg": "pierna", "arm": "brazo",
                  "forearm": "antebrazo", "groin": "ingle", "scalp": "cuero cabelludo", "neck": "cuello",
                  "wound": "herida", "limb": "extremidad", "upper": "superior", "lower": "inferior", "axilla": "axila",
                  "calf": "pantorrilla", "hand": "mano", "foot": "pie", "the": ""}


def _site_es(site):
    """A bleeding site in Spanish word by word ("left thigh" -> "muslo izquierdo"), as far as its words are known."""
    words = [word for word in str(site).split() if word]
    if words and all(word.lower() in _SITE_WORDS_ES for word in words):
        side = [word for word in words if word.lower() in {"left", "right"}]
        rest = [word for word in words if word.lower() not in {"left", "right", "the"}]
        femenine = bool(rest) and rest[-1].lower() in {"leg", "groin", "wound", "limb", "axilla", "calf", "hand"}
        said = " ".join(_SITE_WORDS_ES[word.lower()] for word in rest)
        if side:
            adjective = _SITE_WORDS_ES[side[0].lower()]
            said += " " + (adjective[:-1] + "a" if femenine else adjective)
        article = "la" if femenine else "el"
        return f"{article} {said}".strip()
    return site


def _to(name):
    """'a' before a service, contracted before a masculine article: "al equipo PERT"."""
    return "al " + name[3:] if name.startswith("el ") else "a " + name


# The wall motion a coronary occlusion shows on the scan (acs_reperfusion.wall_motion), said
# whole: word by word it read "mildly reducido contraction" (TD-23, cycle 8).
_WALLS_ES = {"inferior wall": ("La pared inferior", "a"), "lateral wall": ("La pared lateral", "a"),
             "posterior wall": ("La pared posterior", "a"), "anterior wall and apex": ("La pared anterior y el ápex", "o"),
             "anterior and lateral walls": ("Las paredes anterior y lateral", "a")}
_WALL_GRADES_ES = (("contracts normally", "contract normally", "se contrae normalmente", "se contraen normalmente"),
                   ("shows mildly reduced contraction", "show mildly reduced contraction",
                    "muestra una contracción levemente disminuida", "muestran una contracción levemente disminuida"),
                   ("shows moderately reduced contraction", "show moderately reduced contraction",
                    "muestra una contracción moderadamente disminuida",
                    "muestran una contracción moderadamente disminuida"),
                   ("is akinetic", "are akinetic", "está acinética", "están acinétic{}s"))
_WALL_MOTION_RULES = tuple(
    (r"\bThe " + wall + " " + (many if " and " in wall or wall.endswith("walls") else one) + r"\b",
     spanish + " " + (many_es.format(ending) if " and " in wall or wall.endswith("walls") else one_es))
    for wall, (spanish, ending) in _WALLS_ES.items() for one, many, one_es, many_es in _WALL_GRADES_ES) + (
    (r"; the other walls contract normally\b", "; las demás paredes se contraen normalmente"),
    (r"\bContraction is globally normal, without a single focal defect\b",
     "La contracción es globalmente normal, sin un defecto focal único"),
    (r"\bContraction is globally (mildly|moderately|severely) reduced, without a single focal defect\b",
     lambda m: "La contracción está globalmente " + {"mildly": "levemente", "moderately": "moderadamente",
                                                       "severely": "gravemente"}[m[1]] + " disminuida, sin un defecto focal único"),
    # What was not stated when an urgent order ran without its reasoning (TD-23, cycle 8).
    (r"Urgent intervention executed without waiting for the reasoning\. Not stated: (.+?)\. You can explain it "
     r"afterwards; it is recorded as a retrospective explanation\.",
     lambda m: "Intervención urgente ejecutada sin esperar el razonamiento. No se indicó: " + _gate_fields_es(m[1]) +
     ". Puedes explicarlo después; queda registrado como explicación retrospectiva."),
)
# The reasoning gate's questions as the urgent notice lists them (lowercase, without "?").
_GATE_FIELDS_ES = {
    "what do you think is going on": "qué crees que está pasando",
    "which problem are you addressing first (optional)": "qué problema estás abordando primero (opcional)",
    "what do you expect to happen, or what are you trying to clarify": "qué esperas que ocurra o qué buscas aclarar",
    "what will you check, and when": "qué vas a revisar y cuándo",
    "when will you check it": "cuándo lo vas a revisar",
}


def _gate_fields_es(fields):
    # A question may hold a comma of its own ("what will you check, and when"), so each is
    # replaced whole rather than split.
    for english, spanish in _GATE_FIELDS_ES.items():
        fields = fields.replace(english, spanish)
    return fields


#: Phase 0 (closure, F0-11, 2026-10-06): the room's new sentences -- the order ledger's
#: receipts, the look at the bedside, a wait an event cut short, the arrest, a submission
#: stopped part way, an order written after an answer -- said whole in Spanish, before the
#: word rules below can say them by halves. The resident's own words quoted in them stay as
#: written (``_keep_resident_words``): «Stop the infusion», never «Stop infusión de the».
#: Codes, fates and other fields the room does not show are not translated.
_PHASE0_RULES = (
 (r'Not understood: "([^"]*)"\. Nothing was given or done for it\. Write it again in other words if you still '
  r'want it\.',
  r'No se entendió: «\1». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún '
  r'lo quieres.'),
 (r'Not run: "([^"]*)" was written in the answer to the question above, which completes the held order only\. '
  r'Write it again as a new order if you still want it\.',
  r'No se ejecutó: «\1» se escribió en la respuesta a la pregunta anterior, que solo completa la orden retenida. '
  r'Escríbelo de nuevo como una orden nueva si aún lo quieres.'),
 (r'Not executed: "([^"]*)"\. The patient is in cardiac arrest; resuscitation management is not modelled in this '
  r'pilot\.',
  r'No se ejecutó: «\1». El paciente está en paro cardíaco; el manejo de la reanimación no está modelado en este '
  r'piloto.'),
 (r'Recorded as your decision, not given: "([^"]*)"\. This simulator does not model a response to it in this '
  r'case, so nothing changed\.',
  r'Registrado como tu decisión, no administrado: «\1». Este simulador no modela una respuesta a ello en este '
  r'caso, así que nada cambió.'),
 (r'"([^"]*)" in your answer was taken as the held order restated: it runs once, as it was held\.',
  r'«\1» en tu respuesta se tomó como la orden retenida escrita de nuevo: se ejecuta una sola vez, tal como estaba '
  r'retenida.'),
 (r'Not done now: "([^"]*)"\. An order for a later time is not carried out in this pilot: nothing was given and '
  r'nothing was scheduled\. Write it again when you want it done\.',
  r'No se hizo ahora: «\1». En este piloto, una orden para más tarde no se ejecuta: no se administró nada ni se '
  r'programó nada. Escríbela de nuevo cuando quieras que se haga.'),
 (r'Your order "([^"]*)" was interrupted while it was being processed, and nothing of it was applied\. Nothing '
  r"will be repeated automatically: check the patient's state, and send it again if it is still needed\.",
  r'Tu orden «\1» se interrumpió mientras se procesaba, y no se aplicó nada de ella. Nada se repetirá '
  r'automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria.'),
 (r'Your order "([^"]*)" was interrupted while it was being processed, and part of it may have been applied\. '
  r"Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed\.",
  r'Tu orden «\1» se interrumpió mientras se procesaba, y es posible que una parte de ella se haya aplicado. Nada '
  r'se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria.'),
 (r'Also in your answer: "([^"]*)"\. The answer completes the held order only; this order is read next, as an '
  r'order of its own, with its own receipt\.',
  r'También en tu respuesta: «\1». La respuesta solo completa la orden retenida; esta orden se lee a continuación, '
  r'como una orden propia, con su propio recibo.'),
 (r'Part of this order could not be matched to what the simulator did: (.+?)\. Check the patient state before '
  r'relying on it\.',
  r'Parte de esta orden no pudo hacerse corresponder con lo que hizo el simulador: \1. Revisa el estado del '
  r'paciente antes de confiar en ella.'),
 (r'(?i:oxygen non-rebreather mask) ([\d.]+) L/min: no flow was written; the standard non-rebreather flow, '
  r'([\d.]+) L/min, was used\.',
  r'Oxígeno por mascarilla con reservorio a \1 L/min: no se escribió un flujo; se usó el flujo habitual de la '
  r'mascarilla con reservorio, \2 L/min.'),
 # A partly carried-out or partly held order (0B).
 (r'\*\*PART OF THIS ORDER WAS NOT CARRIED OUT\*\*', '**PARTE DE ESTA ORDEN NO SE EJECUTÓ**'),
 (r'\*\*PART OF THIS ORDER IS HELD — CLARIFICATION REQUIRED\*\*',
  '**PARTE DE ESTA ORDEN ESTÁ RETENIDA — SE NECESITA UNA ACLARACIÓN**'),
 (r'Executed now: \*\*(.+?)\*\*\.', r'Ejecutado ahora: **\1**.'),
 (r'Not carried out: \*\*(.+?)\*\*\. Nothing of it has been given; write it again as a new order if you still '
  r'want it\.',
  r'No ejecutado: **\1**. No se ha administrado nada de ello; escríbelo de nuevo como una orden nueva si aún lo '
  r'quieres.'),
 (r'Held until you answer: \*\*(.+?)\*\*\. Nothing of it has been given\.',
  r'Retenido hasta que respondas: **\1**. No se ha administrado nada de ello.'),
 (r'The item below is held until you answer\. Nothing of it has been given\.',
  'El elemento de abajo queda retenido hasta que respondas. No se ha administrado nada de ello.'),
 # Time (0E, 0F): the look at the bedside, the limit of one step, a wait an event cut short.
 (r'On reassessment at the bedside, 1 minute later, ', 'Al reevaluar en la cabecera, 1 minuto después, '),
 (r'On reassessment at the bedside, (\d+) minutes later, ', r'Al reevaluar en la cabecera, \1 minutos después, '),
 (r'\. On reassessment at the bedside 1 minute after the order, ',
  '. Al reevaluar en la cabecera, 1 minuto después de la orden, '),
 (r'\. On reassessment at the bedside (\d+) minutes after the order, ',
  r'. Al reevaluar en la cabecera, \1 minutos después de la orden, '),
 (r'The wait was interrupted after (\d+) minutes? of the (\d+) you asked for, at minute (\d+): (.+?)\. Now, ',
  r'La espera se interrumpió tras \1 min de los \2 que pediste, en el minuto \3: \4. Ahora, '),
 (r'The wait was interrupted after (\d+) minutes?, at minute (\d+): (.+?)\. Now, ',
  r'La espera se interrumpió tras \1 min, en el minuto \2: \3. Ahora, '),
 (r'^Given: (.+?)\. (?=La espera se interrumpió)', r'Administrado: \1. '),
 (r'Specify a reassessment interval from 0 to 120 minutes\. The simulator moves the clock at most 120 minutes in '
  r'one step \(a limit of this pilot\): write a wait or a reassessment of 120 minutes or less, and wait again '
  r'afterwards if you need more time\.',
  'Indica un intervalo de reevaluación de 0 a 120 minutos. El simulador avanza el reloj como máximo 120 minutos '
  'de una vez (un límite de este piloto): escribe una espera o una reevaluación de 120 minutos o menos, y vuelve '
  'a esperar después si necesitas más tiempo.'),
 # The events that cut a wait short (0H), as the update names them.
 (r'\bcomplete atrioventricular block\b', 'bloqueo auriculoventricular completo'),
 (r'\bventricular fibrillation, pulse lost\b', 'fibrilación ventricular, sin pulso'),
 (r'\bcardiac arrest, pulse lost\b', 'paro cardíaco, sin pulso'),
 (r'\bcardiac arrest from uncontrolled haemorrhage\b', 'paro cardíaco por hemorragia no controlada'),
 (r'\bcirculatory arrest from untreated anaphylaxis\b', 'paro circulatorio por anafilaxia no tratada'),
 (r'\bloss of circulation from the falling rate\b', 'pérdida de la circulación por la frecuencia que cae'),
 (r'\bgeneralized seizure\b', 'convulsión generalizada'),
 (r'\bthe anaphylactic reaction returns\b', 'la reacción anafiláctica vuelve'),
 (r'\btension pneumothorax on the ventilator\b', 'neumotórax a tensión con el ventilador'),
 (r'\bmajor bleeding after thrombolysis\b', 'hemorragia mayor tras la trombólisis'),
 (r'\bfrequent ventricular ectopy on dobutamine\b', 'extrasístoles ventriculares frecuentes con dobutamina'),
 (r'\bright ventricle failing under fast volume\b', 'falla del ventrículo derecho con volumen rápido'),
 (r'\bsustained hypotension from the obstruction\b', 'hipotensión sostenida por la obstrucción'),
 (r'\bbrought back after discharge\b', 'traído de vuelta tras el alta'),
 (r'\bsystolic pressure (\d+) mmHg and falling\b', r'presión sistólica de \1 mmHg y en descenso'),
 (r'\bsaturation (\d+) % and falling\b', r'saturación de \1 % y en descenso'),
 (r'\ba critical change\b', 'un cambio crítico'),
 # The arrest (0G): what the room says, what the examination finds and the monitor shows.
 (r'Cardiac arrest occurred at minute (\d+)\. Resuscitation management is not modelled in this pilot\. '
  r'Subsequent management is not assessable\.',
  r'Se produjo un paro cardíaco en el minuto \1. El manejo de la reanimación no está modelado en este piloto. El '
  r'manejo posterior no es evaluable.'),
 (r'Cardiac arrest occurred at an earlier minute\. Resuscitation management is not modelled in this pilot\. '
  r'Subsequent management is not assessable\.',
  'Se produjo un paro cardíaco en un minuto anterior. El manejo de la reanimación no está modelado en este piloto. '
  'El manejo posterior no es evaluable.'),
 (r'Unresponsive, not breathing, no central pulse: the patient is in cardiac arrest\. Resuscitation is not '
  r'modelled in this pilot\.',
  'Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. La reanimación no está '
  'modelada en este piloto.'),
 (r'No pulse: (.+?) on the monitor; no blood pressure; not breathing; unresponsive\.',
  r'Sin pulso: \1 en el monitor; sin presión arterial; sin respiración; sin respuesta.'),
 (r'Ahora, Sin pulso: ', 'Ahora, sin pulso: '),
 (r'\bno organized rhythm\b', 'sin ritmo organizado'),
 (r'\bPulseless ventricular tachycardia\b', 'Taquicardia ventricular sin pulso'),
 (r'\bVentricular fibrillation\b', 'Fibrilación ventricular'),
 (r'\bPulseless electrical activity\b', 'Actividad eléctrica sin pulso'),
 # The anaphylaxis arrest, untreated and after a dose that wore off (0J).
 (r'Circulatory arrest after twenty-five minutes of untreated anaphylaxis\. Adrenaline was the treatment that '
  r'was missing; nothing else that was given acts on the reaction\.',
  'Paro circulatorio tras veinticinco minutos de anafilaxia no tratada. La adrenalina era el tratamiento que '
  'faltaba; nada más de lo administrado actúa sobre la reacción.'),
 (r'Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier had '
  r'worn off and the reaction had come back\. Nothing else that was given acts on the reaction\.',
  'Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes había '
  'perdido su efecto y la reacción había vuelto. Nada más de lo administrado actúa sobre la reacción.'),
)
_RESIDENT_WORDS = re.compile('([-])')


def _keep_resident_words(body):
    """Set aside the resident's words a sentence quotes ("..."), to be put back as they were written."""
    kept = []

    def keep(match):
        if len(kept) >= 0x100:
            return match.group(0)
        kept.append(match.group(1))
        return '"' + chr(0xE300 + len(kept) - 1) + '"'

    return re.sub(r'"([^"\n]{1,500})"', keep, body), kept


_RULES = _PHASE0_RULES + _WALL_MOTION_RULES + (
 # A delivery time longer than this simulator runs (cycle 8); before the word rules below.
 (r"([\d.]+) mL at ([\d.]+) mL/h would run for ([\d.]+) h; this simulator runs a fluid order over at most 120 min\. "
  r"Restate it as a bolus or a shorter infusion\.",
  r"\1 mL a \2 mL/h durarían \3 h; este simulador pasa un fluido en 120 min como máximo. Escríbelo como bolo o "
  r"como una infusión más corta."),
 (r"([\d.]+) mL over ([\d.]+) h: this simulator runs a fluid order over at most 120 min\. Restate it as a bolus or "
  r"a shorter infusion\.",
  r"\1 mL en \2 h: este simulador pasa un fluido en 120 min como máximo. Escríbelo como bolo o como una infusión más "
  r"corta."),
 (r"([\d.]+) units over ([\d.]+) h in all: this simulator runs a transfusion over at most 120 min\. Restate it "
  r"with a shorter time, or transfuse fewer units now\.",
  r"\1 unidades en \2 h en total: este simulador pasa una transfusión en 120 min como máximo. Escríbela con un "
  r"tiempo más corto, o transfunde menos unidades ahora."),
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
 # Whole engine labels first, before the generic words below translate them by
 # halves ("Epinephrine inicio at 0.1", "started as a bolus (no rate written")
 # (2026-09-27: found in the Spanish rehearsal of scenario 19).
 (r"\bSynchronized cardioversion delivered: ", "Cardioversión sincronizada administrada: "),
 (r"\bAirway equipment prepared; intubation has not occurred\b",
  "Equipo de vía aérea preparado; la intubación no se ha realizado"),
 (r"\bstopping crystalloid \((\d+) mL not given\)", r"suspensión del cristaloide (\1 mL sin administrar)"),
 (r"\bwithholding further fluid \(none was running\)", "sin más volumen (no había volumen pasando)"),
 (r" started as a bolus \(no rate written; the simulator's standard rate, about (\d+) mL/min\)",
  r" iniciado en bolo (sin velocidad escrita; velocidad estándar del simulador, unos \1 mL/min)"),
 (r"\((\d+) mL of ([\d.]+) mL infused by ([\d.]+) min; remainder due at ([\d.]+) min\)",
  r"(\1 mL de \2 mL pasados al minuto \3; el resto termina al minuto \4)"),
 (r"(\d mL(?: (?:IV|IO|PO|SC))?) started\b(?! over)", r"\1 iniciado"),
 (r"\b([A-Z][\w -]*?) reviewed; the result already on file is unchanged",
  r"\1: se revisó; el resultado ya registrado no cambia"),
 (r"\b([A-Z][\w -]*?) has been requested and is not back yet; it is expected at (\d+) min",
  r"\1: solicitado, todavía sin resultado; se espera al minuto \2"),
 (r"\b([A-Z][\w -]*?) has not been requested in this encounter", r"\1: no se ha solicitado en este encuentro"),
 (r"\bPelvic binder applied at the greater trochanters; the pelvic volume is (?:reduced|reducido)\b",
  "Faja pélvica aplicada a nivel de los trocánteres mayores; el volumen pélvico se reduce"),
 (r"\bPelvic binder applied at the greater trochanters\b", "Faja pélvica aplicada a nivel de los trocánteres mayores"),
 (r"\b(\d+(?:\.\d+)?) mcg IV bolus\b", r"\1 mcg IV en bolo"),
 (r"\bContinuous nebulized (\w+) running at ([\d.]+) mg/h; unchanged", r"\1 nebulizado continuo a \2 mg/h; sin cambios"),
 (r"\bContinuous nebulized (\w+) adjusted to ([\d.]+) mg/h", r"\1 nebulizado continuo ajustado a \2 mg/h"),
 (r"\bContinuous nebulized (\w+) ([\d.]+) mg/h started", r"\1 nebulizado continuo a \2 mg/h iniciado"),
 (r"\bContinuous nebulized albuterol stopped\b", "Albuterol nebulizado continuo suspendido"),
 (r"\b(start|adjust|continue) at (?=[\d.])",
  lambda m: {"start": "inicio a ", "adjust": "ajuste a ", "continue": "continúa a "}[m.group(1)]),
 (r"; engine convention while the weight type for this drug is undecided\b",
  "; convención del motor mientras el tipo de peso de este fármaco está pendiente"),
 (r"; this is analgesia, not sedation\b", "; esto es analgesia, no sedación"),
 (r"; the atrial rate rises and the ventricular escape does not follow\b",
  "; la frecuencia auricular sube y el escape ventricular no la sigue"),
 (r"\bOral carbohydrate given\b", "Carbohidratos orales administrados"),
 (r"\bDextrose 10% at ([\d.]+) mL/h started\b", r"Dextrose 10% a \1 mL/h iniciada"),
 (r"\bNaloxone infusion at ([\d.]+) mg/h started\b", r"infusión de Naloxone a \1 mg/h iniciada"),
 (r"(\d mg (?:IV|IO|PO|IM|SC)) given: this ECG shows no occlusion pattern, so thrombolysis carries its bleeding "
  r"risk without an artery to open",
  r"\1 administrado: este ECG no muestra un patrón de oclusión, así que la trombólisis tiene su riesgo de "
  r"sangrado sin una arteria que abrir"),
 (r"(\d mg (?:IV|IO|PO|IM|SC)) given: the artery is already open", r"\1 administrado: la arteria ya está abierta"),
 (r"(\d mg (?:IV|IO|PO|IM|SC)) given: reperfusion is expected at minute (\d+)",
  r"\1 administrado: se espera la reperfusión al minuto \2"),
 (r"(\d mg (?:IV|IO|PO|IM|SC)) given\b", r"\1 administrado"),
 (r"\bExercise stress test started\b", "Prueba de esfuerzo iniciada"),
 (r"\bExercise stress test performed: no ischaemic change at the workload achieved\b",
  "Prueba de esfuerzo realizada: sin cambios isquémicos con la carga alcanzada"),
 (r"\b(Needle|Finger|Chest tube) decompression of the (left|right) chest: ",
  lambda m: {"Needle": "Descompresión con aguja", "Finger": "Descompresión digital",
             "Chest tube": "Descompresión con tubo pleural"}[m.group(1)]
  + " del hemitórax " + {"left": "izquierdo", "right": "derecho"}[m.group(2)] + ": "),
 (r"\bChest tube in the (left|right) chest: (\d+) mL of blood drained immediately and it continues to fill",
  lambda m: "Tubo pleural en el hemitórax " + {"left": "izquierdo", "right": "derecho"}[m.group(1)]
  + f": se drenan {m.group(2)} mL de sangre de inmediato y sigue llenándose"),
 (r"no air under tension was released\. A haemothorax is drained with a tube, not a needle",
  "no salió aire a tensión. Un hemotórax se drena con un tubo, no con una aguja"),
 (r"no air under tension was released", "no salió aire a tensión"),
 (r"nothing was released and no blood drained", "no salió aire ni se drenó sangre"),
 (r"the collection is on the other side", "la colección está al otro lado"),
 (r"the pneumothorax is on the other side", "el neumotórax está al otro lado"),
 (r"air under tension released; the pressure and the saturation recover",
  "salió aire a tensión; la presión y la saturación se recuperan"),
 (r"\bVentilator circuit disconnected; the chest is allowed to empty\b",
  "Circuito del ventilador desconectado; se deja vaciar el tórax"),
 (r"\bVentilator settings: ", "Parámetros del ventilador: "),
 (r"\bIntubation completed; invasive ventilation started\b", "Intubación realizada; ventilación invasiva iniciada"),
 (r"\bBag-mask assisted ventilation started\b", "Ventilación asistida con bolsa-mascarilla iniciada"),
 (r"\b(Tourniquet|Direct pressure|Pressure|Packing|Wound packing|Pressure dressing|Hemostatic dressing) applied to "
  r"the ([\w -]+?): the external bleeding is controlled",
  lambda m: _HAEMOSTASIS_ES.get(m.group(1), m.group(1)) + " en " + _site_es(m.group(2))
  + ": el sangrado externo está controlado"),
 # What a measure did, reduced or stopped (TD-31, 2026-09-29). The line above is kept
 # for the records written before, which said «controlled» for both.
 (r"\b(Tourniquet|Direct pressure|Pressure|Packing|Wound packing|Pressure dressing|Hemostatic dressing) applied to "
  r"the ([\w -]+?): the external bleeding (is (?:reduced|reducido), not stopped|"
  r"is stopped; until now it was only (?:reduced|reducido)|is stopped|"
  r"stays (?:reduced|reducido), not stopped; this adds no control to what is already applied|was already stopped)",
  # «reduced» alone is said by an earlier word rule; the sentence is read either way.
  lambda m: _HAEMOSTASIS_ES.get(m.group(1), m.group(1)) + " en " + _site_es(m.group(2)) + ": " + {
      "is reduced, not stopped": "el sangrado externo disminuye, pero no se detiene",
      "is stopped": "el sangrado externo se detiene",
      "is stopped; until now it was only reduced": "el sangrado externo se detiene; hasta ahora sólo disminuía",
      "stays reduced, not stopped; this adds no control to what is already applied":
          "el sangrado externo sigue disminuido, sin detenerse; esto no agrega control a lo ya aplicado",
      "was already stopped": "el sangrado externo ya estaba detenido"}[m.group(3).replace("reducido", "reduced")]),
 (r"\b(Tourniquet|Direct pressure|Pressure|Packing|Wound packing|Pressure dressing|Hemostatic dressing) applied to "
  r"the ([\w -]+?): there is no external source bleeding here",
  lambda m: _HAEMOSTASIS_ES.get(m.group(1), m.group(1)) + " en " + _site_es(m.group(2))
  + ": aquí no hay una fuente de sangrado externo"),
 (r"\bDischarge home already requested; not repeated\b", "Alta a domicilio ya indicada; no se repite"),
 (r"\bED observation for ([\d.]+) h ordered; the period has not been completed\b",
  r"Observación en urgencias por \1 h indicada; el período no se ha completado"),
 (r"\bED observation ordered, with no duration stated\b", "Observación en urgencias indicada, sin duración"),
 (r" \(ordered again\)", " (indicada de nuevo)"),
 (r"\bAdmission to ([\w ]+?) already requested; not repeated\b",
  lambda m: f"Ingreso a {_DESTINATIONS_ES.get(m.group(1), m.group(1))} ya solicitado; no se repite"),
 (r"\badmission to ([\w ]+?) already requested \(not repeated\)",
  lambda m: f"ingreso a {_DESTINATIONS_ES.get(m.group(1), m.group(1))} ya solicitado (no se repite)"),
 (r"\bdischarge home already requested \(not repeated\)", "alta a domicilio ya indicada (no se repite)"),
 (r"\brequesting admission to ([\w ]+?)(?=,|$| \+)",
  lambda m: f"solicitar ingreso a {_DESTINATIONS_ES.get(m.group(1), m.group(1))}"),
 (r"\bdischarging the patient home\b", "dar el alta a domicilio"),
 (r"(?<=Traslado u hospitalización solicitada: )([\w ]+)",
  lambda m: _DESTINATIONS_ES.get(m.group(1).strip(), m.group(1))),
 (r"\b(urinary catheter|nasogastric tube|peripheral intravenous access|continuous monitoring and pulse oximetry"
  r"|nil by mouth) removed\b",
  lambda m: {"urinary catheter": "sonda vesical retirada", "nasogastric tube": "sonda nasogástrica retirada",
             "peripheral intravenous access": "acceso venoso periférico retirado",
             "continuous monitoring and pulse oximetry": "monitorización continua y oximetría de pulso retiradas",
             "nil by mouth": "régimen cero suspendido"}[m.group(1)]),
 (r"\b(urinary catheter|nasogastric tube|continuous monitoring and pulse oximetry|nil by mouth) already in place; "
  r"not repeated",
  lambda m: {"urinary catheter": "sonda vesical ya instalada; no se repite",
             "nasogastric tube": "sonda nasogástrica ya instalada; no se repite",
             "continuous monitoring and pulse oximetry": "monitorización continua y oximetría de pulso ya en curso; no se repite",
             "nil by mouth": "régimen cero ya registrado; no se repite"}[m.group(1)]),
 (r"\bperipheral intravenous access placed\b", "acceso venoso periférico instalado"),
 (r"\bperipheral intravenous access replaced\b", "acceso venoso periférico reemplazado"),
 # An intraosseous line, with its site (C7-06, 2026-09-28).
 (r"\bintraosseous access(?: \((humeral|tibial|sternal|femoral)\))? (placed|removed|already in place; not repeated)\b",
  lambda m: "acceso intraóseo" + (f" ({_IO_SITES_ES[m.group(1)]})" if m.group(1) else "") + " "
  + {"placed": "instalado", "removed": "retirado",
     "already in place; not repeated": "ya instalado; no se repite"}[m.group(2)]),
 (r"The line is recorded as intraosseous\. This simulator gives an intravenous and an intraosseous dose the same "
  r"effect, so nothing else changes\.",
  "La vía queda registrada como intraósea. Este simulador da el mismo efecto a una dosis endovenosa y a una "
  "intraósea, así que nada más cambia."),
 (r"\b(cath lab|" + "|".join(_SERVICES_ES) + r") already contacted \(not repeated\)",
  lambda m: ("hemodinamia" if m.group(1) == "cath lab" else _SERVICES_ES[m.group(1)]) + " ya contactado (no se repite)"),
 (r"\bcontacting (cath lab|" + "|".join(_SERVICES_ES) + r") \(no intervention yet\)",
  lambda m: "contactando " + _to("hemodinamia" if m.group(1) == "cath lab" else _SERVICES_ES[m.group(1)])
  + " (sin intervención aún)"),
 (r"\bWhile awaiting diagnostic results over (\d+) minutes?,", r"Mientras se esperaban los resultados, en \1 minutos,"),
 (r"\bOn immediate reassessment,", "En la reevaluación inmediata,"),
 (r"\bexhausted: shallow and ineffective effort\b", "agotado: esfuerzo superficial e ineficaz"),
 (r"\bExhausted: shallow and ineffective effort\b", "Agotado: esfuerzo superficial e ineficaz"),
 # The guided completion of a held order: its labels, never the resident's words between them.
 (r"\*\*Working model:\*\*", "**Modelo de trabajo:**"),
 (r"\*\*Management priority:\*\*", "**Prioridad de manejo:**"),
 (r"\*\*Expected effect:\*\*", "**Efecto esperado:**"),
 (r"\*\*Reassessment:\*\* (.*?) in (\d+) minutes", r"**Reevaluación:** \1 en \2 minutos"),
 (r"\*\*Reassessment:\*\* (.*?) in \[time\] minutes", r"**Reevaluación:** \1 en [tiempo] minutos"),
 # What an order recognised and did not execute (unexecuted_items), the resident's words quoted.
 (r"Blood product ordered and recorded as your decision: (.+?)\. Its physiologic effect is not modelled in this "
  r"simulator: the order stands in the record, and the patient's course does not include its effect\.",
  "Hemoderivado indicado y registrado como tu decisión: \u00ab\\1\u00bb. Su efecto fisiológico no está modelado en "
  "este simulador: la indicación queda en el registro, y la evolución del paciente no incluye su efecto."),
 (r"Massive transfusion protocol activation recorded: (.+?)\. Activating it gives no blood product by itself; the "
  r"units given are the ones ordered\.",
  "Activación del protocolo de transfusión masiva registrada: \u00ab\\1\u00bb. Activarlo no administra ningún "
  "hemoderivado por sí solo; las unidades administradas son las que se indican."),
 (r"Also in this order, a blood product whose physiologic effect is not modelled: (.+?)\.(?=\n|$)",
  "También en esta orden, un hemoderivado cuyo efecto fisiológico no está modelado: \u00ab\\1\u00bb."),
 (r"Also in this order, the massive transfusion protocol's activation: (.+?)\.(?=\n|$)",
  "También en esta orden, la activación del protocolo de transfusión masiva: \u00ab\\1\u00bb."),
 (r"Massive transfusion protocol stood down and recorded as your decision: (.+?)\. No unit already given is taken "
  r"back\.",
  "Desactivación del protocolo de transfusión masiva registrada como tu decisión: \u00ab\\1\u00bb. Ninguna unidad "
  "ya administrada se revierte."),
 (r"Also in this order, the massive transfusion protocol stood down: (.+?)\.(?=\n|$)",
  "También en esta orden, la desactivación del protocolo de transfusión masiva: \u00ab\\1\u00bb."),
 (r"Indicated and recorded as your decision: (.+?)\. Its administration and effect are not modelled in this "
  r"simulator, so nothing was given and nothing changed\.",
  "Indicado y registrado como tu decisión: \u00ab\\1\u00bb. Su administración y su efecto no están modelados en "
  "este simulador, así que no se administró nada y nada cambió."),
 (r"Prescription for home recorded: (.+?)\. It is a prescription, not a dose given here\.",
  "Receta para el domicilio registrada: \u00ab\\1\u00bb. Es una receta, no una dosis administrada aquí."),
 (r"Recorded as a conditional plan, not executed now: (.+?)\.$",
  "Registrado como plan condicional, no ejecutado ahora: \u00ab\\1\u00bb."),
 (r"Recorded as a disposition plan, not carried out now: (.+?)\. The patient stays in the emergency department; a "
  r"plan is not carried out on its own\.",
  "Registrado como plan de destino, no realizado ahora: \u00ab\\1\u00bb. El paciente sigue en urgencias; un plan no "
  "se realiza por sí solo."),
 (r"Recorded as a repeat instruction, not executed now: (.+?)\.$",
  "Registrado como instrucción de repetición, no ejecutada ahora: \u00ab\\1\u00bb."),
 (r"Recorded as advice to the patient: (.+?)\.$", "Registrado como indicación al paciente: \u00ab\\1\u00bb."),
 (r"Recorded as treatment received before your care, as reported: (.+?)\. It is part of the history, not your "
  r"order: nothing was given now\.",
  "Registrado como tratamiento recibido antes de tu atención, según lo informado: \u00ab\\1\u00bb. Es parte de la "
  "historia, no tu orden: no se administró nada ahora."),
 # Whole sentences before the word-by-word rule below, which would otherwise
 # leave them half translated ("None of it was administrado").
 (r"None of it was administered\.", "No se administró nada de ella."),
 (r"The held order is still waiting:", "La orden retenida sigue esperando:"),
 (r"the order above", "la orden de arriba"),
 (r"Answer the question above, or say cancel\.", "Responde la pregunta de arriba o escribe «cancelar»."),
 (r"Nothing has been administered\.", "No se ha administrado nada."),
 # "Tranexamic acid 1 g IV administered over 10 min" (C08, cycle 6).
 (r"\badministered over (\d+(?:[.,]\d+)?) min\b", r"administrado en \1 min"),
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
 (r"\b(\d+) units started\b", r"\1 unidades iniciadas"), (r"\b1 unit started\b", "1 unidad iniciada"),
 (r"\bnormal saline\b", "suero fisiológico"), (r"\bNormal saline\b", "Suero fisiológico"),
 (r"\blactated Ringer's\b", "Ringer lactato"),
 (r"\bstarted over (\d+) min\b", r"a pasar en \1 min"),
 (r"\bTransfer/admission requested: ", "Traslado u hospitalización solicitada: "),
 (r"\bDischarge home requested\b", "Alta a domicilio indicada"),
 (r"\bcath lab activated\b", "hemodinamia activada"),
 # A consult to any other service, and the same consult asked for again
 # (2026-09-26: the label stayed in English whatever the reading language).
 (r"\b(" + "|".join(_SERVICES_ES) + r") contacted; definitive intervention has not yet occurred",
  lambda m: f"Se contactó {_to(_SERVICES_ES[m.group(1)])}; la intervención definitiva todavía no ocurre"),
 (r"\b(" + "|".join(_SERVICES_ES) + r") already contacted at minute (\d+); not repeated",
  lambda m: f"Ya se había contactado {_to(_SERVICES_ES[m.group(1)])} en el minuto {m.group(2)}; no se repite"),
 (r"Write the total dextrose: the grams, or the concentration with the total volume\. (\d+(?:\.\d+)?) ampoules "
  r"with (\d+(?:\.\d+)?) mL may mean \2 mL in all or in each\.",
  r"Indica la glucosa total: los gramos, o la concentración con el volumen total. \1 ampollas con \2 mL pueden "
  r"ser \2 mL en total o en cada una."),
 (r"\bcath lab contacted for angiography\b", "hemodinamia contactada para coronariografía"),
 (r"\bcath lab already contacted at minute (\d+); not repeated",
  r"Ya se había contactado a hemodinamia en el minuto \1; no se repite"),
 (r"\bcath lab contacted\b", "hemodinamia contactada"),
 (r"; definitive intervention has not yet occurred\b", "; la intervención definitiva todavía no ocurre"),
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
 # A clause joined to what the prehospital team did (DF-22, C08, 2026-09-28).
 (r'"([^"]+)" is written with what the prehospital team did, so it was not given\.',
  r'«\1» está escrito junto a lo que hizo el equipo prehospitalario, así que no se administró.'),
 (r"If it is your order now, write it as your order, or say cancel\.",
  "Si ahora es tu orden, escríbela como orden tuya, o di cancelar."),
 (r"These orders were not recognized:", "Estas órdenes no se reconocieron:"),
 (r"Replace each with a supported intervention, dose/settings and route, or say cancel\.",
  "Reemplaza cada una por una intervención soportada, con dosis o parámetros y vía, o di cancelar."),
 (r"This order was also not recognized:", "Esta orden tampoco se reconoció:"),
 (r"These orders were also not recognized:", "Estas órdenes tampoco se reconocieron:"),
 # --- an infusion rate far outside the range, and the second antiplatelet ---
 (r"([\d.]+) (mcg/min|mcg/kg/min) is ([\d.]+) times the supported maximum\.",
  r"\1 \2 es \3 veces el máximo soportado."),
 (r"([\d.]+) (mcg/min|mcg/kg/min) is below the supported minimum\.",
  r"\1 \2 está bajo el mínimo soportado."),
 (r"This encounter runs (\w+) between ([\d.]+) and ([\d.]+) (mcg/min|mcg/kg/min)\.",
  r"Este encuentro administra \1 entre \2 y \3 \4."),
 (r"A rate written in mg is one thousand times the same number in mcg; confirm the intended (\w+) rate in (mcg/min|mcg/kg/min)\.",
  r"Una velocidad escrita en mg es mil veces el mismo número en mcg; confirma la velocidad de \1 en \2."),
 (r"(\w+) is already on board\. Dual antiplatelet therapy is aspirin plus one P2Y12 inhibitor, so (\w+) would be a second one rather than a change\.",
  r"\1 ya está administrado. La antiagregación dual es aspirina más un inhibidor P2Y12, así que \2 sería un segundo inhibidor y no un cambio."),
 (r"Stop (\w+) explicitly if you mean to replace it\.",
  r"Suspende \1 explícitamente si tu intención es reemplazarlo."),
 (r"The held order was discarded to run this one:", "La orden retenida se descartó para ejecutar esta:"),
 (r"Before execution, please add:", "Antes de ejecutarla, agrega:"),
 (r"Use your own words, or complete the guided sentence starters on screen\.",
  "Usa tus propias palabras, o completa los inicios de frase en pantalla."),
 (r"You do not need to repeat the order\.", "No necesitas repetir la orden."),
 # What a held order also carries, by kind (unexecuted_items.held_messages).
 (r"Also in this order, indicated with administration and effect not modelled: (.+?)\.(?=\n|$)",
  "También en esta orden, indicado sin modelar su administración ni su efecto: «\\1»."),
 (r"Also in this order, a prescription for home: (.+?)\.(?=\n|$)",
  "También en esta orden, una receta para el domicilio: «\\1»."),
 (r"Also in this order, a conditional plan: (.+?)\.(?=\n|$)",
  "También en esta orden, un plan condicional: «\\1»."),
 (r"Also in this order, a disposition plan: (.+?)\.(?=\n|$)",
  "También en esta orden, un plan de destino: «\\1»."),
 (r"Also in this order, a repeat instruction: (.+?)\.(?=\n|$)",
  "También en esta orden, una instrucción de repetición: «\\1»."),
 (r"Also in this order, advice to the patient: (.+?)\.(?=\n|$)",
  "También en esta orden, una indicación al paciente: «\\1»."),
 (r"Also in this order, treatment received before your care: (.+?)\.(?=\n|$)",
  "También en esta orden, un tratamiento recibido antes de tu atención: «\\1»."),
 # --- investigations -------------------------------------------------------
 # The additional-lead ECGs (acs_reperfusion.additional_leads), whole.
 (r"\bRight-sided leads V3R and V4R, recorded alongside the standard twelve\.",
  "Derivaciones derechas V3R y V4R, registradas junto con las doce estándar."),
 (r"\bPosterior leads V7, V8 and V9, recorded alongside the standard twelve\.",
  "Derivaciones posteriores V7, V8 y V9, registradas junto con las doce estándar."),
 (r"ST elevation of 1\.5 mm in V4R, with 1 mm in V3R\. The inferior elevation is unchanged in this tracing\.",
  "Supradesnivel del ST de 1.5 mm en V4R, con 1 mm en V3R. El supradesnivel inferior no cambia en este trazado."),
 (r"The V4R elevation has resolved since the artery was opened\.",
  "El supradesnivel en V4R se resolvió desde que se abrió la arteria."),
 (r"No ST elevation in V3R or V4R\.", "Sin supradesnivel del ST en V3R ni V4R."),
 (r"ST elevation of 1 mm in V7 to V9, concordant with the reciprocal depression already present anteriorly\.",
  "Supradesnivel del ST de 1 mm en V7 a V9, concordante con el infradesnivel recíproco ya presente en la cara anterior."),
 (r"The posterior elevation has resolved since the artery was opened\.",
  "El supradesnivel posterior se resolvió desde que se abrió la arteria."),
 (r"No ST elevation in V7, V8 or V9\.", "Sin supradesnivel del ST en V7, V8 ni V9."),
 (r"Textual report: this encounter records the additional leads in words; the rendered tracing shows the standard "
  r"twelve\.", "Informe en texto: este encuentro registra las derivaciones adicionales por escrito; el trazado "
  "dibujado muestra las doce estándar."),
 (r"The fluid was given faster than the obstructed right ventricle can accept: it distends, the septum shifts and "
  r"the output falls\. Volume here is given slowly and in small amounts, or not at all\.",
  "El volumen se administró más rápido de lo que el ventrículo derecho obstruido puede recibir: se distiende, el "
  "tabique se desplaza y el gasto cae. Aquí el volumen se da lento y en pequeñas cantidades, o no se da."),
 # The fixed structure of every study report (family_reports, pocus_report):
 # its names, its field labels and the POCUS sections. With a case's findings
 # in Spanish (case_text), an English label left beside them would make the
 # very mixed line decision 16 objects to (2026-09-26). Each label is anchored
 # where the report writes it, never inside the findings.
 (r"\bPOCUS · performed at minute (\d+(?:\.\d+)?)", r"POCUS · realizada en el minuto \1"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))HEART(?=$| — )", "CORAZÓN"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))INFERIOR VENA CAVA(?=$| — )", "VENA CAVA INFERIOR"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))LUNGS(?=$| — )", "PULMONES"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))VEINS · COMPRESSION(?=$| — )", "VENAS · COMPRESIÓN"),
 (r"(?m)^ADDITIONAL FINDINGS$", "HALLAZGOS ADICIONALES"),
 (r"(?:(?<=\| )|(?<=: ))Additional findings — ", "Hallazgos adicionales — "),
 (r"(?<=· |— )LV contractility: ", "Contractilidad del VI: "),
 (r"(?<=· |— )RV size and relation to LV: ", "Tamaño del VD y relación con el VI: "),
 (r"(?<=· |— |: )Pericardium: ", "Pericardio: "),
 (r"(?<=· |— |: )IVC: ", "VCI: "),
 (r"(?<=· |— )Pleural sliding: ", "Deslizamiento pleural: "),
 (r"(?<=· |— )B-lines: ", "Líneas B: "),
 (r"(?<=· |— )Consolidation and pleural effusion: ", "Consolidación y derrame pleural: "),
 (r"(?<=· |— )Aortic root: ", "Raíz aórtica: "),
 (r"(?<=· |— )Descending thoracic aorta: ", "Aorta torácica descendente: "),
 (r"(?<=· |— )Abdominal aorta: ", "Aorta abdominal: "),
 (r"(?<=· |— )Femoral veins: ", "Venas femorales: "),
 (r"(?<=· |— )Popliteal veins: ", "Venas poplíteas: "),
 # The E-FAST window by window (TD-48, faculty, 2026-10-02): its titles and labels, anchored as the
 # POCUS's. A window that states the case's own findings stays whole in English until the case's
 # translation is approved (TD-46).
 (r"\bE-FAST · performed at minute (\d+(?:\.\d+)?)", r"E-FAST · realizado en el minuto \1"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))RIGHT UPPER QUADRANT(?=$| — )", "CUADRANTE SUPERIOR DERECHO"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))LEFT UPPER QUADRANT(?=$| — )", "CUADRANTE SUPERIOR IZQUIERDO"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))SUPRAPUBIC(?=$| — )", "SUPRAPÚBICA"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))SUBXIPHOID(?=$| — )", "SUBXIFOIDEA"),
 (r"(?m)(?:^|(?<=\| )|(?<=: ))LUNG(?=$| — )", "PULMÓN"),
 (r"(?<=· |— )Morison's pouch \(hepatorenal\): ", "Espacio de Morison (hepatorrenal): "),
 (r"(?<=· |— )Right subdiaphragmatic space: ", "Espacio subdiafragmático derecho: "),
 (r"(?<=· |— )Right pleural recess: ", "Receso pleural derecho: "),
 (r"(?<=· |— )Splenorenal space: ", "Espacio esplenorrenal: "),
 (r"(?<=· |— )Left subdiaphragmatic space: ", "Espacio subdiafragmático izquierdo: "),
 (r"(?<=· |— )Left pleural recess: ", "Receso pleural izquierdo: "),
 (r"(?<=· |— )Longitudinal view: ", "Vista longitudinal: "),
 (r"(?<=· |— )Transverse view: ", "Vista transversal: "),
 (r"(?<=· |— )Right lung sliding: ", "Deslizamiento pulmonar derecho: "),
 (r"(?<=· |— )Left lung sliding: ", "Deslizamiento pulmonar izquierdo: "),
 (r"(?<=· |— )M-mode: ", "Modo M: "),
 (r"(?<=: )Not documented\b", "No documentado"),
 # What the engine writes into a POCUS it recomputes (the bleeding patient's
 # filling, 2026-09-29; positive pressure): a case's own passages come first,
 # from its approved translation, and these say the rest in the same words.
 (r"\b(\d+(?:\.\d+)?) cm; complete inspiratory collapse\b", r"\1 cm; colapso inspiratorio completo"),
 (r"\b(\d+(?:\.\d+)?) cm; near-complete inspiratory collapse\b", r"\1 cm; colapso inspiratorio casi completo"),
 (r"\b(\d+(?:\.\d+)?) cm; >50% inspiratory collapse\b", r"\1 cm; colapso inspiratorio >50%"),
 (r"\b(\d+(?:\.\d+)?) cm; about 50% inspiratory collapse\b", r"\1 cm; colapso inspiratorio de aproximadamente 50%"),
 (r"\b(\d+(?:\.\d+)?) cm; <50% inspiratory collapse\b", r"\1 cm; colapso inspiratorio <50%"),
 (r"\b(\d+(?:\.\d+)?) cm; respiratory variation not assessable during positive-pressure support\b",
  r"\1 cm; variación respiratoria no evaluable durante el soporte con presión positiva"),
 (r"\bSmall cavity with hyperdynamic contraction; ", "Cavidad pequeña con contracción hiperdinámica; "),
 (r"\bSmall cavity with normal contraction; ", "Cavidad pequeña con contracción normal; "),
 (r"(?<=; )complete obliteration of the cavity in systole\b", "obliteración completa de la cavidad en sístole"),
 (r"(?<=; )near-obliteration of the cavity in systole\b", "obliteración casi completa de la cavidad en sístole"),
 (r"(?<=; )no obliteration in systole\b", "sin obliteración en sístole"),
 (r"\bCavity of normal size with hyperdynamic contraction\b", "Cavidad de tamaño normal con contracción hiperdinámica"),
 (r"\bCavity of normal size with normal contraction\b", "Cavidad de tamaño normal con contracción normal"),
 (r"(?<=· |: )LV: ", "VI: "), (r"(?<=· |: )RV: ", "VD: "), (r"(?<=· |: )Lungs: ", "Pulmones: "),
 (r"(?<=· |: )Finding: ", "Hallazgo: "), (r"(?<=· |: )History: ", "Historia: "),
 (r"\bFree T4 \(ng/dL\)", "T4 libre (ng/dL)"), (r"\bBase excess \(mmol/L\)", "Exceso de base (mmol/L)"),
 (r"\bValue \(mmol/L\)", "Valor (mmol/L)"), (r"\bP/F ratio\b", "Relación P/F"),
 (r"\bWBC \(K/µL\)", "Leucocitos (K/µL)"), (r"\bPlatelets \(K/µL\)", "Plaquetas (K/µL)"),
 (r"\bCreatinine \(mg/dL\)", "Creatinina (mg/dL)"), (r"\bGlucose \(mg/dL\)", "Glucosa (mg/dL)"),
 (r"\bCRP \(mg/L\)", "PCR (mg/L)"),
 (r"\bThyroid function\b", "Pruebas tiroideas"), (r"\bKetones\b", "Cetonas"),
 (r"(?m)^Toxicology:", "Panel toxicológico:"),
 (r"\bRenal tract ultrasound\b", "Ecografía renal y de vías urinarias"),
 (r"\bPelvis X-ray\b", "Radiografía de pelvis"),
 (r"(?m)^Investigation:", "Examen:"),
 (r"\bNo tracing could be acquired\.", "No se pudo obtener un trazado."),
 (r"\bNo result has been recorded\.", "No se ha registrado ningún resultado."),
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
 (r"\bHead CT\b", "Tomografía de cerebro"), (r"\bAbdominal CT\b", "Tomografía de abdomen"),
 (r"\bBlood group and crossmatch\b", "Grupo y pruebas cruzadas"),
 (r"\bPregnancy test\b", "Prueba de embarazo"),
 (r"\bUrine culture\b", "Urocultivo"),
 (r"\bRight-sided ECG \(V3R-V4R\)", "ECG con derivaciones derechas (V3R-V4R)"),
 (r"\bPosterior ECG \(V7-V9\)", "ECG con derivaciones posteriores (V7-V9)"),
 (r"\bGlucose (\d+) mg/dL", r"Glucosa \1 mg/dL"),
 # The age-adjusted rule reads before the plain one: rules apply in order.
 (r"Age-adjusted upper reference: (\d+) ng/mL FEU up to (\d+) years, age x 10 above it\.",
  r"Referencia superior ajustada por edad: \1 ng/mL FEU hasta los \2 años, y edad x 10 por encima."),
 (r"Above the limit: this does not establish a diagnosis and does not exclude one\.",
  "Sobre el límite: esto no establece un diagnóstico ni lo descarta."),
 (r"At or below the limit for this age\.", "En el límite o por debajo para esta edad."),
 (r"\bUpper reference, age-adjusted\b", "Referencia superior ajustada por edad"),
 (r"\bD-dimer\b", "Dímero D"),
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
 (r"\bSTUDY REQUESTED\b", "ESTUDIO SOLICITADO"),
 (r"\bREASONING COMPLETION\b", "COMPLETAR EL RAZONAMIENTO"),
 (r"\bCONTEXT CHECK — DOES NOT BLOCK EXECUTION\b", "REVISIÓN DE CONTEXTO — NO BLOQUEA LA EJECUCIÓN"),
 (r"^YOU$", "TÚ"), (r"^PROTOTYPE$", "PROTOTIPO"),
 # --- the bedside panel and the page's own chrome ---------------------------
 # --- weight and height in the chart (2026-09-27) ---------------------------
 (r"^Weight and height$", "Peso y talla"),
 (r"^Weight not recorded$", "Peso no registrado"), (r"^Height not recorded$", "Talla no registrada"),
 (r"^Weight ([\d.]+) kg \(", r"Peso \1 kg ("), (r"^Height ([\d.]+) m \(", r"Talla \1 m ("),
 (r"^Previous dry weight ([\d.]+) kg \(", r"Peso seco previo \1 kg ("),
 (r"; not today's weight\)$", "; no es el peso de hoy)"),
 (r"\bmeasured at triage\b", "medido en el triage"), (r"\bmeasured on the bed scale\b", "medido en la balanza de la camilla"),
 (r"\breported by the patient\b", "referido por el paciente"),
 (r"\breported by his daughter\b", "referido por su hija"), (r"\breported by her son\b", "referido por su hijo"),
 (r"\breported by his partner\b", "referido por su pareja"), (r"\breported by her partner\b", "referido por su pareja"),
 (r"\breported by his wife\b", "referido por su esposa"), (r"\breported by her spouse\b", "referido por su cónyuge"),
 (r"\bestimated by the team; the patient could not be weighed\b", "estimado por el equipo; no se pudo pesar al paciente"),
 (r"\bestimated by the team\b", "estimado por el equipo"), (r"\brecorded in the case\b", "registrado en el caso"),
 (r"his dialysis unit's record, before the two missed sessions",
  "registro de su unidad de diálisis, antes de las dos sesiones perdidas"),
 (r"^(Talla [\d.]+ m \()(medid|referid|estimad)o\b", r"\1\2a"),
 # --- the reader's weight questions and the weight each dose used (2026-09-27) ---
 (r"This order is written per kilogram and the patient's weight is not recorded\. What does the patient weigh, "
  r"in kg\? The whole order is kept; only the weight is missing\.",
  "Esta orden está escrita por kilo y el peso del paciente no está registrado. ¿Cuánto pesa el paciente, en kg? "
  "La orden completa queda en espera; sólo falta el peso."),
 (r"Give the patient's weight in kg \(for example, 60 kg\)\. The whole order is kept; only the weight is missing\.",
  "Indica el peso del paciente en kg (por ejemplo, 60 kg). La orden completa queda en espera; sólo falta el peso."),
 (r" (?:is|are) written per kilogram and no weight type was named\. This patient's actual weight is well above "
  r"the ideal weight, so the dose depends on which is meant: ",
  ": la dosis está escrita por kilo y no se indicó qué peso usar. El peso real de este paciente supera bastante "
  "al ideal, así que la dosis depende de cuál se quiso decir: "),
 (r"\. Which weight should (?:it|they) use\? The whole order is kept; nothing has run\.",
  ". ¿Qué peso uso? La orden completa queda en espera; nada se ha ejecutado."),
 (r"Say which weight this dose should use: actual, ideal or adjusted \(or give the weight in kg\)\. The whole "
  r"order is kept; nothing has run\.",
  "Indica qué peso usar para esta dosis: real, ideal o ajustado (o el peso en kg). La orden completa queda en "
  "espera; nada se ha ejecutado."),
 (r" names the (actual|ideal|predicted|adjusted|lean) body weight, but the height is not recorded, so it cannot be "
  r"calculated\. What weight should this dose use, in kg\? The whole order is kept; nothing has run\.",
  r" nombra el peso \1, pero la talla no está registrada y no se puede calcular. ¿Qué peso uso para esta dosis, "
  r"en kg? La orden completa queda en espera; nada se ha ejecutado."),
 (r"(\d(?:\.\d+)? (?:mg|mcg|mL|units|g)/kg(?:/\w+)?),? and (?=\w+ [\d.]+ )", r"\1 y "),
 (r"\bactual ([\d.]+) kg\b", r"real \1 kg"), (r"\badjusted ([\d.]+) kg\b", r"ajustado \1 kg"),
 (r"\bactual body weight\b", "peso real"), (r"\bideal body weight\b", "peso ideal"),
 (r"\bpredicted body weight\b", "peso predicho"), (r"\badjusted body weight\b", "peso ajustado"),
 (r"\blean body weight\b", "peso magro"), (r"\bprevious dry weight\b", "peso seco previo"),
 (r" \(duration on the actual weight, ([\d.]+) kg\)", r" (duración medida sobre el peso real, \1 kg)"),
 (r"; chosen earlier for this drug\b", "; elegido antes para este fármaco"),
 (r"\bthe weight the resident gave for this drug\b", "el peso que indicaste para este fármaco"),
 (r"\bthe weight the resident gave\b", "el peso que indicaste"),
 (r"\bthe weight written with the order\b", "el peso escrito en la orden"),
 (r"\bthe chart records ([\d.]+) kg\b", r"la ficha registra \1 kg"),
 (r"\bon the (peso \w+)", r"sobre el \1"),
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
 (r"Systemic thrombolysis given in obstructive shock, a hypotension with signs of hypoperfusion: the obstruction begins to fall within minutes and keeps falling for about half an hour\.",
  "Trombólisis sistémica administrada en shock obstructivo, una hipotensión con signos de hipoperfusión: la obstrucción empieza a ceder en minutos y sigue cediendo por media hora."),
 (r"Systemic thrombolysis given for sustained hypotension \(15 consecutive minutes\): the obstruction begins to fall within minutes and keeps falling for about half an hour\.",
  "Trombólisis sistémica administrada por hipotensión sostenida (15 minutos consecutivos): la obstrucción empieza a ceder en minutos y sigue cediendo por media hora."),
 (r"Systemic thrombolysis given without the hemodynamic indication: systolic (\d+) mmHg with no sign of hypoperfusion, low for (\d+) of the 15 consecutive minutes a hypotension without them requires\. The bleeding risk is taken without the indication, and the obstruction is unchanged\.",
  r"Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de \1 mmHg sin signos de hipoperfusión, baja durante \2 de los 15 minutos consecutivos que exige una hipotensión sin ellos. Se asume el riesgo de sangrado sin la indicación, y la obstrucción no cambia."),
 (r"Systemic thrombolysis given without the hemodynamic indication: systolic (\d+) mmHg on a vasopressor the pressure does not need, with no hypotension from the embolism\. The bleeding risk is taken without the indication, and the obstruction is unchanged\.",
  r"Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de \1 mmHg con un vasopresor que la presión no necesita, sin hipotensión por la embolia. Se asume el riesgo de sangrado sin la indicación, y la obstrucción no cambia."),
 (r"Systemic thrombolysis given without the hemodynamic indication: systolic (\d+) mmHg, with no hypotension from the embolism\. The bleeding risk is taken without the indication, and the obstruction is unchanged\.",
  r"Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de \1 mmHg, sin hipotensión por la embolia. Se asume el riesgo de sangrado sin la indicación, y la obstrucción no cambia."),
 (r"A second systemic thrombolytic dose is recorded; the first was given at minute (\d+)\. A persisting shock does not by itself indicate repeating a full dose, and this simulator gives the repeated dose no effect of its own\.",
  r"Se registra una segunda dosis de trombolítico sistémico; la primera se dio en el minuto \1. Un shock que persiste no indica por sí solo repetir una dosis completa, y este simulador no le da a la dosis repetida un efecto propio."),
 # P-04 and P-05 (faculty, 2026-09-30): what the drug does, never what it will achieve, and
 # the rest of a regimen apart from a second course. The notes above stay for older records.
 (r"Systemic thrombolysis given in obstructive shock, a hypotension with signs of hypoperfusion\. The drug acts on the clot over about half an hour; what it changes is seen on reassessment\.",
  "Trombólisis sistémica administrada en shock obstructivo, una hipotensión con signos de hipoperfusión. El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar."),
 (r"Systemic thrombolysis given for sustained hypotension \(15 consecutive minutes\)\. The drug acts on the clot over about half an hour; what it changes is seen on reassessment\.",
  "Trombólisis sistémica administrada por hipotensión sostenida (15 minutos consecutivos). El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar."),
 (r"Systemic thrombolysis given without the hemodynamic indication: systolic (\d+) mmHg with no sign of hypoperfusion, low for (\d+) of the 15 consecutive minutes a hypotension without them requires\. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment\.",
  r"Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de \1 mmHg sin signos de hipoperfusión, baja durante \2 de los 15 minutos consecutivos que exige una hipotensión sin ellos. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar."),
 (r"Systemic thrombolysis given without the hemodynamic indication: systolic (\d+) mmHg on a vasopressor the pressure does not need, with no hypotension from the embolism\. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment\.",
  r"Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de \1 mmHg con un vasopresor que la presión no necesita, sin hipotensión por la embolia. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar."),
 (r"Systemic thrombolysis given without the hemodynamic indication: systolic (\d+) mmHg, with no hypotension from the embolism\. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment\.",
  r"Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de \1 mmHg, sin hipotensión por la embolia. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar."),
 (r"(\w+) ([\d.]+) mg recorded as part of the initial regimen begun at minute (\d+) \(([\d.]+) mg in all\)\. It completes the first dose rather than starting a new one, and the first dose keeps acting as before\.",
  lambda m: f"Se registran {m.group(2)} mg de {_thrombolytic_es(m.group(1))} como parte del esquema inicial comenzado en el "
            f"minuto {m.group(3)} ({m.group(4)} mg en total): completan la primera dosis en lugar de iniciar una nueva, y "
            "la primera dosis sigue actuando como antes."),
 (r"A second course of systemic thrombolysis is recorded \(([^)]+)\); the first course began at minute (\d+)\. Its added bleeding risk is recorded as exposure\. This simulator represents neither additional reperfusion from a second course nor any bleeding of its own; that is a simplification, not evidence that repeating has no effect\. The first dose keeps acting as before\.",
  lambda m: f"Se registra un segundo curso de trombólisis sistémica ({_thrombolytic_es(m.group(1))}); el primero comenzó en "
            f"el minuto {m.group(2)}. Su riesgo adicional de sangrado queda registrado como exposición. Este simulador no "
            "representa una reperfusión adicional por un segundo curso ni un sangrado propio; es una simplificación, no "
            "evidencia de que repetir no tenga efecto. La primera dosis sigue actuando como antes."),
 # D-4 (faculty, 2026-10-02): the whole criterion in the note -- the vasopressor and hypoperfusion of shock, recognised
 # as soon as present, and the fifteen minutes only for a hypotension without those signs.
 (r"Systemic thrombolysis given in obstructive shock: systolic below 90 mmHg, or a vasopressor needed to reach 90 mmHg, with signs of hypoperfusion\. In shock it is indicated as soon as the shock is present; the 15 consecutive minutes apply only to a hypotension without those signs\. The drug acts on the clot over about half an hour; what it changes is seen on reassessment\.",
  "Trombólisis sistémica administrada en shock obstructivo: sistólica bajo 90 mmHg, o un vasopresor necesario para llegar "
  "a 90 mmHg, con signos de hipoperfusión. En shock está indicada desde que el shock está presente; los 15 minutos "
  "consecutivos aplican sólo a una hipotensión sin esos signos. El fármaco actúa sobre el trombo durante cerca de media "
  "hora; lo que cambie se ve al reevaluar."),
 (r"Systemic thrombolysis given for sustained hypotension: systolic below 90 mmHg, or a vasopressor needed to keep it at 90 mmHg or above, for 15 consecutive minutes\. The drug acts on the clot over about half an hour; what it changes is seen on reassessment\.",
  "Trombólisis sistémica administrada por hipotensión sostenida: sistólica bajo 90 mmHg, o un vasopresor necesario para "
  "mantenerla en 90 mmHg o más, durante 15 minutos consecutivos. El fármaco actúa sobre el trombo durante cerca de media "
  "hora; lo que cambie se ve al reevaluar."),
 # D-5 (faculty, 2026-10-02): the bleeding note, which had no Spanish.
 (r"Bleeding from (the surgical site operated on twelve days ago|an uncontrolled arterial pressure|the declared site): the haemoglobin is falling\. This is the risk the thrombolytic carries, and it was taken in a patient who had a reason to bleed\.",
  lambda m: "Sangrado " + {"the surgical site operated on twelve days ago": "del sitio operado hace doce días",
                           "an uncontrolled arterial pressure": "por una presión arterial no controlada",
                           "the declared site": "del sitio declarado"}[m.group(1)]
            + ": la hemoglobina está bajando. Es el riesgo que conlleva el trombolítico, y se asumió en una persona "
              "que tenía un motivo para sangrar."),
 (r"The systolic pressure has stayed below 90 mmHg for 15 consecutive minutes: this is sustained hypotension from the obstruction\.",
  "La presión sistólica se ha mantenido bajo 90 mmHg por 15 minutos consecutivos: esto es hipotensión sostenida por la obstrucción."),
 (r"The systolic pressure has needed a vasopressor to stay at 90 mmHg or above, or stayed below it, for 15 consecutive minutes: this is sustained hypotension from the obstruction\.",
  "La presión sistólica ha necesitado un vasopresor para mantenerse en 90 mmHg o más, o se ha mantenido bajo ese valor, por 15 minutos consecutivos: esto es hipotensión sostenida por la obstrucción."),
 (r"Systemic thrombolysis given for sustained hypotension: the obstruction begins to fall within minutes and keeps falling for about half an hour\.",
  "Trombólisis sistémica administrada por hipotensión sostenida: la obstrucción empieza a ceder en minutos y sigue cediendo por media hora."),
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
 # A study recognised and not modelled (2026-09-24). The study's own name is
 # translated by the label table below; the sentence around it here.
 (r"Study requested; not modelled in this version of the simulator: (.+?)\. The request is recorded "
  r"with its time; no result will be produced and none is invented\.",
  r"Estudio solicitado; no modelado en esta versión del simulador: \1. La solicitud queda "
  r"registrada con su hora; no habrá resultado y no se inventa ninguno."),
 (r"Not available in this service: (.+?)\. ", r"No disponible en este servicio: \1. "),
 (r"Specify which blood product to give and how many units\.",
  "Indica qué hemoderivado quieres administrar y cuántas unidades."),
 (r"Write each blood product with its own number of units\.",
  "Escribe cada hemoderivado con su propio número de unidades."),
 (r"Specify whether to transfuse these units now, with the number of units, or to request a "
  r"crossmatch to have them reserved\.",
  "Indica si quieres transfundir estas unidades ahora, con el número de unidades, o pedir "
  "grupo y pruebas cruzadas para dejarlas reservadas."),
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
 (r"\bperipheral intravenous access replaced\b", "acceso venoso periférico reemplazado"),
 (r"The dextrose does not run: the forearm swells around the cannula and the infusion slows to a stop\. "
  r"What was ordered is not what reached the patient\.",
  "La glucosa no pasa: el antebrazo se hincha alrededor del catéter y la infusión se detiene. "
  "Lo que se indicó no es lo que llegó al paciente."),
 (r"The new line runs freely\. What is given now reaches the circulation\.",
  "La vía nueva pasa sin resistencia. Lo que se administre ahora llega a la circulación."),
 # The line as a property of the access (DC2 to DC5, 2026-09-29): what the bedside shows.
 (r"A peripheral intravenous cannula is already in place in the left forearm\.",
  "Ya tiene instalada una cánula venosa periférica en el antebrazo izquierdo."),
 # The neutral arrival line (faculty, 2026-09-29): that a line exists, not who placed it.
 (r"Peripheral IV in place in the left forearm\.",
  "Vía venosa periférica instalada en el antebrazo izquierdo."),
 (r"As it goes in, the skin around the forearm cannula swells\.",
  "Mientras pasa, la piel alrededor de la cánula del antebrazo se hincha."),
 (r"A new peripheral cannula is placed in the right forearm\.",
  "Se instala una cánula periférica nueva en el antebrazo derecho."),
 (r"An intraosseous needle is placed\.", "Se instala una aguja intraósea."),
 (r"An intraosseous needle is placed to give this dose, at minute (\d+); the order names no site\.",
  r"Se instala una aguja intraósea para dar esta dosis, en el minuto \1; la orden no indica el sitio."),
 (r"The dextrose 10% infusion at ([\d.]+) mL/h runs through the (cannula in the left forearm|new cannula in the right "
  r"forearm|intraosseous needle) from minute (\d+)\.",
  lambda m: f"La infusión de suero glucosado al 10 % a {m.group(1)} mL/h pasa por " + {
      "cannula in the left forearm": "la cánula del antebrazo izquierdo",
      "new cannula in the right forearm": "la cánula nueva del antebrazo derecho",
      "intraosseous needle": "la aguja intraósea"}[m.group(2)] + f" desde el minuto {m.group(3)}."),
 # R-4 terminology (faculty, 2026-09-30): «aumento de volumen», «dolor a la palpación», «suero glucosado».
 (r"Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness\.",
  "Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la palpación."),
 (r"Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender\.",
  "Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y "
  "doloroso a la palpación."),
 (r"Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool\.",
  "Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de "
  "volumen y fría."),
 (r"A second peripheral cannula in the right forearm; the site is clean\.",
  "Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio."),
 (r"An intraosseous needle in place \((humeral|tibial|sternal|femoral)\)\.",
  lambda m: f"Una aguja intraósea instalada ({_IO_SITES_ES[m.group(1)]})."),
 (r"An intraosseous needle in place; no site was recorded\.",
  "Una aguja intraósea instalada; no se registró el sitio."),
 (r"Dextrose 10% runs at ([\d.]+) mL/h through the (cannula in the left forearm|new cannula in the right forearm|"
  r"intraosseous needle)\.",
  lambda m: f"El suero glucosado al 10 % pasa a {m.group(1)} mL/h por " + {
      "cannula in the left forearm": "la cánula del antebrazo izquierdo",
      "new cannula in the right forearm": "la cánula nueva del antebrazo derecho",
      "intraosseous needle": "la aguja intraósea"}[m.group(2)] + "."),
 (r"\bcontinuous monitoring and pulse oximetry started\b", "monitorización continua y oximetría de pulso iniciadas"),
 (r"\bnil by mouth recorded\b", "régimen cero registrado"),
 (r"\burinary catheter placed\b", "sonda vesical instalada"),
 (r"\bnasogastric tube placed\b", "sonda nasogástrica instalada"),
 (r"transcutaneous pacing stopped", "marcapasos transcutáneo suspendido"),
 (r"movement is abolished for about (\d+) minutes( \([^)]*\))?\. It does not sedate and it does not relieve pain\.",
  r"el movimiento queda abolido por unos \1 minutos\2. No seda y no quita el dolor."),
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
 (r"([\w-]+) is an NSAID and this patient (.+?)\. The analgesia is real and so is the risk; "
  r"the decision is whether this is the drug for this patient\.",
  r"\1 es un AINE y este paciente \2. La analgesia es real y el riesgo también; la decisión es "
  r"si este es el fármaco para este paciente."),
 (r"\bhas a creatinine of ([\d.]+) mg/dL\b", r"tiene una creatinina de \1 mg/dL"),
 (r"\bis not perfusing well\b", "no está perfundiendo bien"),
 (r"\bis bleeding from the gut\b", "está sangrando del tubo digestivo"),
 # The reasons are joined in English; this fires only between two that have
 # already been said in Spanish.
 (r"\band\b(?=\s+(?:no está|está|tiene una creatinina))", "y"),
 (r"([\w-]+) on top of ([\w-]+): two NSAIDs are one class\. The second adds the risks and very little of the effect\.",
  r"\1 sobre \2: dos AINE son una sola clase. El segundo suma los riesgos y muy poco del efecto."),
 (r"(\w+) already given at minute (\d+); not repeated", r"\1 ya administrado en el minuto \2; no se repite"),
)
_COMPILED = tuple((re.compile(pattern), replacement) for pattern, replacement in _RULES)


#: The bank cases' narrative the faculty approved in another language
#: (``case_text.install``), kept per case: {language: {case: (pattern, table)}},
#: longest first, so a sentence is replaced entirely or not at all -- never half
#: one language (faculty, 2026-09-26). Cases share many sentences; each case reads
#: only its own table, so approving one case never turns another one's lines Spanish.
#: The thrombolytics the reader knows, as the Spanish room names them (D-5, faculty, 2026-10-02).
_THROMBOLYTICS_ES = {"alteplase": "alteplasa", "tenecteplase": "tenecteplasa", "streptokinase": "estreptoquinasa",
                     "thrombolytic": "trombolítico"}


def _thrombolytic_es(words):
    """``alteplase 100 mg`` as ``alteplasa 100 mg``: the drug in Spanish, the dose as written."""
    return re.sub(r"[A-Za-z]+", lambda m: _THROMBOLYTICS_ES.get(m.group(0).lower(), m.group(0)), str(words))


_NARRATIVE = {}
#: The case whose narrative is being presented: the room's (``narrate``, once per
#: run) or a document's (``narrating``). Without one, nothing is replaced.
_CASE = ContextVar("narrated_case", default=None)


def set_narrative(tables, language="es"):
    """Install the approved passages of each case: {case: {English: translation}}.

    Each passage is matched whole, as words: longest first, and never inside a
    longer word, so a one-word passage cannot rewrite part of another word.
    """
    compiled = {}
    for case, table in (tables or {}).items():
        if not table:
            continue
        ordered = sorted(table, key=len, reverse=True)
        pattern = re.compile("|".join(rf"(?<!\w){re.escape(english)}(?!\w)" for english in ordered))
        compiled[case] = (pattern, dict(table))
    _NARRATIVE[language] = compiled


def narrate(case):
    """The case the room presents in this script run; set on every run, before anything is drawn."""
    _CASE.set(str(case or "") or None)


@contextmanager
def narrating(case):
    """Present the narrative of ``case`` inside this block: a document names its own encounter's case."""
    token = _CASE.set(str(case or "") or None)
    try:
        yield
    finally:
        _CASE.reset(token)


#: Whole sentences the engine adds to a case's narrative block (the arrival line of the
#: hypoglycaemia configurations). They follow the case: Spanish where its narrative is
#: approved, English where it is not, so the block reads in one language.
ENGINE_SENTENCES = {"es": {
    "Peripheral IV in place in the left forearm.": "Vía venosa periférica instalada en el antebrazo izquierdo.",
    "A peripheral intravenous cannula is already in place in the left forearm.":
        "Ya tiene instalada una cánula venosa periférica en el antebrazo izquierdo.",
}}


def narrative(text, language=None, case=None):
    """The approved translation of the case's own passages within this text; the rest untouched."""
    language = language or current()
    if language == "en" or not text:
        return text
    installed = _NARRATIVE.get(language, {}).get(case or _CASE.get() or "")
    if not installed:
        return text
    pattern, table = installed
    said = pattern.sub(lambda match: table[match.group(0)], str(text))
    for english, translated in ENGINE_SENTENCES.get(language, {}).items():
        said = said.replace(english, translated)
    return said


#: The examination findings the engine composes from the observations
#: (family_engine.examination_finding, patient_appearance.appearance_summary).
_EXPRESSION_ES = {"neutral": "neutra", "uncomfortable": "incómoda", "markedly uncomfortable": "muy incómoda",
                  "passive": "pasiva", "sedated": "sedada"}
# "flushed" (the anaphylaxis family, 2026-09-23) had no Spanish, and the 29f and 63m summary stayed
# whole in English (pre-pilot closure, 2026-10-02).
_SKIN_ES = {"natural": "natural", "mild pallor": "palidez leve", "pallor": "palidez", "flushed": "enrojecimiento"}
#: Whole sentences the engine adds to an examination region (TD-59, 2026-10-02): the bleeding wound in
#: "General appearance" once something has been applied to it, in the words the room uses for it.
_EXAMINATION_SENTENCES_ES = {
    "The external bleeding is reduced, not stopped.": "El sangrado externo está disminuido, sin detenerse.",
    "The external bleeding is stopped.": "El sangrado externo está detenido.",
    # Every region after an arrest (Phase 0, 0G; closure F0-11).
    "Unresponsive, not breathing, no central pulse: the patient is in cardiac arrest. Resuscitation is not "
    "modelled in this pilot.":
    "Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. La reanimación no está "
    "modelada en este piloto.",
}
_SWEAT_ES = {"absent": "ausente", "mild": "leve", "marked": "marcada"}


def _in_sentence(value, language):
    """An observed value inside a Spanish sentence: lower case, an acronym kept."""
    said = observed_value(str(value).strip(), language)
    return said if said.isupper() else said[:1].lower() + said[1:]


def _appearance(parts, language):
    names = {"Mental status": "Estado mental", "Expression": "Expresión", "Color": "Color", "Diaphoresis": "Diaforesis"}
    tables = {"Expression": _EXPRESSION_ES, "Color": _SKIN_ES, "Diaphoresis": _SWEAT_ES}
    said = []
    for part in parts:
        if part == "Mottling on visible extremities":
            said.append("Moteado en las extremidades visibles")
            continue
        name, _, value = part.partition(": ")
        if name not in names:
            return None
        table = tables.get(name)
        if table is not None and value not in table:
            return None
        said.append(names[name] + ": " + (table[value] if table is not None else observed_value(value, language)))
    return ". ".join(said) + "."


def _neurological_tail(tail, language, case):
    """The pupils and limbs the engine quotes from the case's own neurological passage, from its approved translation."""
    import re as _re
    tail = tail.strip()
    if not tail:
        return ""
    installed = _NARRATIVE.get(language, {}).get(case or _CASE.get() or "")
    if installed:
        for english, spanish in installed[1].items():
            fragments = [bit.strip(" .") for bit in _re.split(r"(?<=[.!?])\s+", tail) if bit.strip(" .")]
            if fragments and all(bit in english for bit in fragments):
                # The same kinds of finding the English quoted, and no more.
                kinds = []
                if _re.search(r"\bpupils?\b", tail, flags=_re.I):
                    kinds.append(r"pupilas?")
                if _re.search(r"lateraliz|lateralis|focal|limbs", tail, flags=_re.I):
                    kinds.append(r"moviliza|sin déficit")
                found = _re.findall(r"\b(?:" + "|".join(kinds) + r")[^.!?;]*[.!?]?", spanish, flags=_re.I) if kinds else []
                if found:
                    return " " + ". ".join(bit[:1].upper() + bit[1:].strip().rstrip(",.") for bit in found) + "."
    return " " + tail


def case_words(text, language=None, case=None):
    """What the case says (history answers, presentation): its approved passages, or a fixed message whole."""
    language = language or current()
    if language == "en" or not text:
        return text
    return MESSAGES.get(str(text).strip()) or narrative(str(text), language, case)


def examination(text, language=None, case=None):
    """An examination finding in the reading language, whole.

    The case's own passages as the faculty approved them (``narrative``); the
    findings the engine composes from the observations ("Respiratory rate: 30/min.
    Work of breathing: Increased") from their templates. Anything else stays as
    written rather than being translated by halves.
    """
    import re as _re
    language = language or current()
    if language == "en" or not text:
        return text
    if "\n" in str(text):
        # "General appearance" is the engine's summary and, below it, what the case wrote that still
        # holds (TD-59, 2026-10-02): each line is said whole in one language, on its own.
        return "\n".join(examination(line, language, case) for line in str(text).split("\n"))
    body = narrative(str(text), language, case).strip()
    if body in _EXAMINATION_SENTENCES_ES:
        return _EXAMINATION_SENTENCES_ES[body]
    match = _re.fullmatch(r"Respiratory rate: ([\d.]+|—)/min\. Work of breathing: (.+)", body)
    if match:
        return f"Frecuencia respiratoria: {match[1]}/min. Trabajo respiratorio: {_in_sentence(match[2], language)}"
    if body == "Pulse absent. Capillary refill is not measurable.":
        return "Pulso ausente. El llene capilar no es medible."
    match = _re.fullmatch(r"Capillary refill: ([\d.]+|—) s\. Extremities: (.+)", body)
    if match:
        return f"Llene capilar: {match[1]} s. Extremidades: {_in_sentence(match[2], language)}"
    match = _re.fullmatch(r"Capillary refill ([\d.]+|not measured) s; extremities (.+)\.", body)
    if match:
        refill = "no medido" if match[1] == "not measured" else match[1] + " s"
        return f"Llene capilar {refill}; extremidades {_in_sentence(match[2], language)}."
    match = _re.fullmatch(r"([^.:]+)\. Respiratory effort: (.+)\.", body)
    if match:
        return (f"{observed_value(match[1], language)}. Esfuerzo respiratorio: "
                f"{_in_sentence(match[2], language)}.")
    match = _re.fullmatch(r"Current mental status: ([^.]+)\.( The patient engages in conversation and follows "
                          r"commands\.| Engagement is reduced; interpret alongside respiratory and circulatory "
                          r"findings\.)(.*)", body, flags=_re.S)
    if match:
        engaged = ("El paciente conversa y obedece órdenes." if "engages" in match[2] else
                   "La interacción está disminuida; interprétala junto con los hallazgos respiratorios y circulatorios.")
        return (f"Estado mental actual: {_in_sentence(match[1], language)}. {engaged}"
                + _neurological_tail(match[3], language, case))
    parts = [part.strip() for part in body.rstrip(".").split(". ")]
    appearance = _appearance(parts, language) if parts and all(
        part.startswith(("Mental status: ", "Expression: ", "Color: ", "Diaphoresis: "))
        or part == "Mottling on visible extremities" for part in parts) else None
    return appearance or body


#: TD-46 (faculty, 2026-09-30): the case's own POCUS and E-FAST findings. A line
#: that still carries one of them in English -- no approved translation of the
#: case replaced it -- is shown whole in English, its label included, instead of
#: being translated word by word into a line of two languages. The findings the
#: engine composes are not the case's words and are said as before.
_STUDY_REPORTS = ("pocus", "efast")
_STUDY_WORDS = {}
_KEPT_LINE = re.compile("\ue000([\ue100-\uefff])\ue001")


def _study_words(case):
    """The English of one bank case's POCUS and E-FAST findings; none for any other case."""
    if case not in _STUDY_WORDS:
        try:
            from clinical_cases import variant_by_id
            investigations = variant_by_id(case).get("investigations") or {}
        except KeyError:
            investigations = {}
        _STUDY_WORDS[case] = frozenset(
            value.strip() for study in _STUDY_REPORTS
            for value in ((investigations.get(study) or {}).get("result") or {}).values()
            if isinstance(value, str) and value.strip())
    return _STUDY_WORDS[case]


def _keep_case_findings(body):
    """Set aside, whole, each line of the text that still states the case's findings in English.

    A line is a report line ("· LV contractility: …"), or one section of the
    compact form ("HEART — … · …"), which the Management Trace joins with " | ".
    """
    case = _CASE.get()
    words = _study_words(case) if case else frozenset()
    if not words:
        return body, []
    kept = []

    def keep(segment):
        parts = segment.split(" · ")
        if not any(part.strip() in words or part.partition(": ")[2].strip() in words for part in parts):
            return segment
        if len(kept) >= 0xE00:
            return segment
        kept.append(segment)
        return "\ue000" + chr(0xE100 + len(kept) - 1) + "\ue001"

    lines = body.split("\n")
    return "\n".join(" | ".join(keep(segment) for segment in line.split(" | ")) for line in lines), kept


def say(text, language=None):
    """Present a stored English string in the reading language."""
    language = language or current()
    if language == "en" or not text:
        return text
    body = narrative(str(text), language)
    exact = MESSAGES.get(body.strip())
    if exact:
        return exact
    body, kept = _keep_case_findings(body)
    for sentence, translation in MESSAGES.items():
        if sentence in body:
            body = body.replace(sentence, translation)
    body, quoted = _keep_resident_words(body)
    for pattern, replacement in _COMPILED:
        body = pattern.sub(replacement, body)
    if quoted:
        body = _RESIDENT_WORDS.sub(lambda match: quoted[ord(match.group(1)) - 0xE300], body)
    if kept:
        body = _KEPT_LINE.sub(lambda match: kept[ord(match.group(1)) - 0xE100], body)
    return body
