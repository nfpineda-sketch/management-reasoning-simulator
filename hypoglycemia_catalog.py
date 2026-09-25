"""The hypoglycaemia catalogue: three axes over mechanisms the engine already executes.

Faculty authorisation of 2026-09-25 (stages 0-2). The three bank cases are
expressed here as configurations, and the catalogue composes the other nine
combinations of its three axes -- mechanism, venous access and severity -- from
them. Nothing here adds a clinical capability: every condition a configuration
can carry is one the bank engine already runs (``glucose_rescue``).

What this module is the single source of:

* the engine flags each case carries (``case_arguments``), which
  ``clinical_cases`` turns into the bank's variants;
* the cues that make a condition discoverable, shared with the gate of
  generated cases through ``glucose_rescue`` and ``case_cues``;
* the evaluation declarations (``declaration_inputs``), which
  ``case_assessment_bank`` turns into opportunities and critical events;
* the compatibilities, typed as the faculty asked: relations necessary for
  the model's coherence, assumptions of one configuration, and the engine's
  simplifications and parameters, each with the review it has had.

**The nine compositions are not offered to residents.** They are review
candidates: the resident's usual selection and a faculty member's case
direction read only the bank (``clinical_cases.FAMILIES``); a candidate opens
only when a faculty member or an administrator chooses it in the sandbox.

**Priority of this family** (faculty, 2026-09-25): recognise and correct the
hypoglycaemia, check the response, and when it is not what was expected, check
the line and what actually reached the patient. Remembering thiamine where it
belongs is a second objective; its omission alone is not a critical event, and
the engine gives no established Wernicke encephalopathy and no immediate
neurological deterioration for it (faculty decision 8, 2026-09-21).
"""
from copy import deepcopy

import case_catalog
import glucose_rescue
from case_cues import affirmed

FAMILY = "hypoglycemia"
VERSION = "1.0.0"

AXES = {
    "mechanism": {
        "es": "Mecanismo", "en": "Mechanism",
        "values": {
            "insulin": {"es": "Insulina", "en": "Insulin"},
            "sulfonylurea": {"es": "Sulfonilurea", "en": "Sulfonylurea"},
            "alcohol_fasting": {"es": "Alcohol y ayuno", "en": "Alcohol and fasting"},
        },
    },
    "iv_access": {
        "es": "Acceso venoso", "en": "Venous access",
        "values": {
            "working": {"es": "Vía funcionante", "en": "Working line"},
            "failed": {"es": "Vía fallida", "en": "Failed line"},
        },
    },
    "severity": {
        "es": "Gravedad", "en": "Severity",
        # Bands of the engine, not a clinical classification: both need
        # someone else's help, which a clinical scale would call severe.
        "values": {
            "severe": {"es": "Severa: glucosa bajo el umbral de convulsión del motor",
                       "en": "Severe: glucose below the engine's seizure threshold"},
            "moderate": {"es": "Moderada: glucosa en la banda somnolienta del motor",
                         "en": "Moderate: glucose in the engine's drowsy band"},
        },
    },
}

# The engine's own thresholds, never restated: glucose_rescue owns them.
_DROWSY = dict((state, threshold) for threshold, state in glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE)["Drowsy"]
_ALERT = dict((state, threshold) for threshold, state in glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE)["Alert"]
_OBTUNDED = dict((state, threshold) for threshold, state in glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE)["Obtunded"]
SEVERITY_BANDS = {
    # [lower, upper) in mg/dL.
    "severe": (_OBTUNDED, glucose_rescue.SEIZURE_GLUCOSE),
    "moderate": (_DROWSY, _ALERT),
}
# The arrival glucose a composed moderate case carries. A value, not a band:
# a composition has to be one reproducible patient. Pending faculty review.
MODERATE_ARRIVAL_GLUCOSE = 52

CONDITIONS = {
    "sulfonylurea_effect": {
        "engine": "recurrence_risk", "values": (True, False), "status": "implemented",
        "decision_relevant": True, "implemented_by": "glucose_rescue.drift_per_min, glucose_rescue.octreotide_active",
        "es": "Efecto de sulfonilurea: la glucosa vuelve a caer hasta que el octreótido lo detiene",
    },
    "endogenous_insulin": {
        "engine": "endogenous_insulin", "values": (True, False), "status": "implemented",
        "decision_relevant": True, "implemented_by": "glucose_rescue.step (rebote tras sobrecorrección)",
        "es": "Secreción propia de insulina: una sobrecorrección sobre 200 mg/dL provoca un rebote",
    },
    "glycogen_depleted": {
        "engine": "glycogen_depleted", "values": (True, False), "status": "implemented",
        "decision_relevant": True, "implemented_by": "glucose_rescue.treatment_gain (glucagón al 30 %)",
        "es": "Reservas de glucógeno agotadas: el glucagón moviliza poco",
    },
    "thiamine_deficient": {
        "engine": "thiamine_deficient", "values": (True, False), "status": "implemented",
        "decision_relevant": True,
        "implemented_by": "sin efecto fisiológico (decisión docente 8, 2026-09-21); oportunidad de evaluación",
        "es": "Déficit probable de tiamina: segundo objetivo del manejo",
    },
    "iv_access_failed": {
        "engine": "iv_access_failed", "values": (True, False), "status": "implemented",
        "decision_relevant": True,
        "implemented_by": "glucose_rescue.delivered_share; family_engine (vascular_access)",
        "es": ("La vía con que llega no está en la vena: de la glucosa en bolo que se da por ella llega el 15 % "
               "(el alcance de la decisión 8; DC4)"),
    },
    "diabetes": {
        "engine": None, "values": ("type_1", "type_2", "none"), "status": "implemented",
        "decision_relevant": False, "implemented_by": "relato (historia y comorbilidades)",
        "es": "Diabetes declarada en la historia",
    },
    "arrival_glucose": {
        "engine": "baseline_glucose", "values": None, "status": "implemented",
        "decision_relevant": False, "implemented_by": "family_engine._initialize (glucosa basal)",
        "es": "Glucosa al llegar (mg/dL)",
    },
    "arrival_mental_status": {
        "engine": None, "values": ("Alert", "Drowsy", "Obtunded", "Unresponsive"), "status": "implemented",
        "decision_relevant": False, "implemented_by": "estado observable autorado al llegar",
        "es": "Estado de conciencia autorado al llegar",
    },
}

_COLLATERAL_WORDS = ("Patient",)


def _history_text(configuration):
    history = configuration["narrative"]["history"]
    parts = [history["chief"], *history["symptoms"], history["medical"], history["medications"],
             history["onset"], history["risks"], *history["focused"].values()]
    parts += list(configuration["narrative"]["examination"].values())
    return " ".join(str(part) for part in parts if part)


def _band_of(glucose):
    for band, (lower, upper) in SEVERITY_BANDS.items():
        if lower <= glucose < upper:
            return band
    return None


def _n1(c):
    if (c["axes"]["mechanism"] == "sulfonylurea") != bool(c["conditions"]["sulfonylurea_effect"]):
        return "The sulfonylurea mechanism and the sulfonylurea effect must come together."


def _n2(c):
    if c["conditions"]["sulfonylurea_effect"] and not c["conditions"]["endogenous_insulin"]:
        return "A sulfonylurea acts through the patient's own insulin; this configuration has none."


def _n3(c):
    if c["axes"]["mechanism"] == "alcohol_fasting" and not c["conditions"]["glycogen_depleted"]:
        return "Hypoglycaemia of alcohol and fasting is one of depleted glycogen; this configuration declares full stores."


def _n4(c):
    if (c["axes"]["iv_access"] == "failed") != bool(c["conditions"]["iv_access_failed"]):
        return "The venous-access axis and the engine's failed-line state must agree."


def _n5(c):
    band = _band_of(c["conditions"]["arrival_glucose"])
    if band != c["axes"]["severity"]:
        lower, upper = SEVERITY_BANDS[c["axes"]["severity"]]
        return (f"A {c['axes']['severity']} configuration arrives with a glucose in [{lower}, {upper}) mg/dL; "
                f"this one arrives with {c['conditions']['arrival_glucose']}.")


def _n6(c):
    if c["conditions"]["sulfonylurea_effect"] and not affirmed(c["narrative"]["history"]["medications"],
                                                              (glucose_rescue.SULFONYLUREA_NAMES,)):
        return "The sulfonylurea must be named among the medicines the resident can ask about."


def _n7(c):
    if c["conditions"]["thiamine_deficient"] and not affirmed(_history_text(c), glucose_rescue.ALCOHOL_OR_STARVATION):
        return "A thiamine deficiency must be discoverable: the history has to state the alcohol or the fasting."


def _n8(c):
    if c["conditions"]["glycogen_depleted"] and not affirmed(_history_text(c), GLYCOGEN_DEPLETION_CUES):
        return "Depleted glycogen must be discoverable: the history has to state days of eating almost nothing."


def _n9(c):
    mental = c["conditions"]["arrival_mental_status"]
    if mental != "Alert" and c["narrative"]["history_source"] in _COLLATERAL_WORDS:
        return "A patient who is not alert needs a collateral source for the history."


def _s1(c):
    if c["conditions"]["diabetes"] == "type_1" and c["conditions"]["endogenous_insulin"]:
        return "In this model type 1 diabetes has no insulin secretion of its own."


# Days without food, as the history says it. Separate from the thiamine cues
# because drinking alone depletes thiamine and not glycogen.
GLYCOGEN_DEPLETION_CUES = (r"\b(?:eaten|eating) (?:almost )?nothing\b", r"\bnothing to eat\b",
                           r"\bpoor (?:oral )?intake\b", r"\bmalnourish\w*\b", r"\bdesnutri\w*\b")

RELATIONS = (
    {"id": "N1", "kind": "necessary", "check": _n1,
     "es": "La sulfonilurea es el mecanismo si y sólo si el caso trae su efecto (la glucosa que vuelve a caer).",
     "why": "El motor representa la sulfonilurea sólo por ese efecto (recurrence_risk)."},
    {"id": "N2", "kind": "necessary", "check": _n2,
     "es": "Una sulfonilurea supone secreción propia de insulina.",
     "why": "Actúa liberando la insulina del propio paciente; sin ella no tendría sobre qué actuar."},
    {"id": "N3", "kind": "necessary", "check": _n3,
     "es": "La hipoglicemia por alcohol y ayuno supone glucógeno agotado.",
     "why": "Es la definición del mecanismo: sin reservas agotadas el alcohol solo no la produce."},
    {"id": "N4", "kind": "necessary", "check": _n4,
     "es": "El eje de acceso venoso y el estado de vía fallida del motor coinciden.",
     "why": "El eje es el estado del motor, no una etiqueta aparte."},
    {"id": "N5", "kind": "necessary", "check": _n5,
     "es": "La gravedad es la banda del motor en que cae la glucosa de llegada.",
     "why": "Las bandas se derivan de los umbrales de glucose_rescue; no se reescriben."},
    {"id": "N6", "kind": "necessary", "check": _n6,
     "es": "Si hay efecto de sulfonilurea, el fármaco se nombra entre los medicamentos.",
     "why": "Descubribilidad: la misma regla que la compuerta de los casos generados."},
    {"id": "N7", "kind": "necessary", "check": _n7,
     "es": "Si hay déficit de tiamina, la historia dice el alcohol o el ayuno.",
     "why": "Descubribilidad: la misma regla que la compuerta de los casos generados."},
    {"id": "N8", "kind": "necessary", "check": _n8,
     "es": "Si el glucógeno está agotado, la historia dice los días sin comer.",
     "why": "Descubribilidad: el residente puede saber por qué el glucagón moviliza poco."},
    {"id": "N9", "kind": "necessary", "check": _n9,
     "es": "Un paciente que no está alerta tiene una fuente colateral para la historia.",
     "why": "La misma exigencia que el banco verifica en todos sus casos."},
    {"id": "S1", "kind": "simplification", "check": _s1,
     "es": "En diabetes tipo 1 no hay secreción propia de insulina (se ignora la secreción residual).",
     "why": "Simplificación del modelo; pendiente de revisión clínica."},
    {"id": "A1", "kind": "assumption", "check": None,
     "es": "El tipo de diabetes se declara en cada configuración; no se deduce del mecanismo.",
     "why": "Una insulina o una sulfonilurea pueden aparecer sin diabetes (exposición accidental o facticia)."},
    {"id": "A2", "kind": "assumption", "check": None,
     "es": "Las reservas de glucógeno se declaran en cada configuración; la diabetes tipo 1 no las fija.",
     "why": "Un paciente con tipo 1 que lleva días sin comer puede tenerlas agotadas: es una condición del escenario."},
    {"id": "A3", "kind": "assumption", "check": None,
     "es": "El déficit de tiamina se declara en cada configuración; el alcohol no lo impone.",
     "why": "Es un riesgo, no una certeza: una configuración de alcohol y ayuno puede no tenerlo."},
)

# Engine parameters as they stand: a technical reference for the battery, never
# a criterion a resident is assessed against, reviewed or not
# (docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md). ``review`` says what the
# repository records about each: "reviewed" is a teaching magnitude the faculty
# reviewed (docs/HYPOGLYCEMIA_MAGNITUDES.md, 2026-09-20), "decided" a faculty
# decision with no magnitude of its own, "pending" a number nobody has reviewed.
REVIEW_STATES = {"reviewed": "Magnitud revisada", "decided": "Decisión docente, sin magnitud",
                 "pending": "Pendiente de revisión"}
_MAGNITUDES_2026_09_20 = "Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md)."
SIMPLIFICATIONS = (
    {"id": "P1", "parameter": "glucose_rescue.drift_per_min",
     "es": "Caída espontánea de 0,08 mg/dL/min, igual para toda insulina y toda dosis; 0,6 mg/dL/min con sulfonilurea hasta el octreótido.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P2", "parameter": "glucose_rescue.SEIZURE_GLUCOSE, SEIZURE_AFTER_MIN, POST_ICTAL_MIN",
     "es": "Convulsión tras 20 minutos acumulados bajo 40 mg/dL; el reloj se reinicia al subir de 40; 10 minutos postictales.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P3", "parameter": "glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE",
     "es": "La conciencia depende sólo de la glucosa: alerta ≥70, somnoliento 45–69, obnubilado 25–44, sin respuesta <25.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P4", "parameter": "family_engine._minute (4 mg/dL por gramo, 10 g por minuto)",
     "es": "Una ampolla de 25 g sube la glucosa unos 100 mg/dL en unos 3 minutos.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P5", "parameter": "glucose_rescue.GLUCAGON_*, GLYCOGEN_*, DEPLETED_GLYCOGEN_SHARE",
     "es": "Glucagón: inicio a los 10 min, 1,6 mg/dL/min por 25 min; la segunda dosis moviliza la mitad y la tercera nada; con glucógeno agotado, 30 %.",
     "review": "pending",
     "review_es": ("La cinética y las dosis repetidas se revisaron el 2026-09-20; el 30 % con glucógeno agotado se "
                   "implementó con la decisión 8 (docs/DECISIONES_3_4_8_MAGNITUDES.md) y esa magnitud no tiene "
                   "revisión registrada.")},
    {"id": "P6", "parameter": "glucose_rescue.ORAL_*",
     "es": "Carbohidrato oral sólo si está alerta: inicio a los 5 min, 1,2 mg/dL/min por 25 min.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P7", "parameter": "glucose_rescue.INFUSION_G_PER_ML",
     "es": "Glucosado al 10 %: 100 mL/h suman 0,67 mg/dL/min.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P8", "parameter": "glucose_rescue.REBOUND_*",
     "es": "Con secreción propia, una glucosa sobre 200 provoca a los 30 min una caída extra de 0,8 mg/dL/min hasta bajar de 100.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P9", "parameter": "glucose_rescue.OCTREOTIDE_*",
     "es": "Octreótido de 25 a 500 mcg: inicio a los 15 min, dura 360 min y detiene por completo la caída de la sulfonilurea.",
     "review": "reviewed", "review_es": _MAGNITUDES_2026_09_20},
    {"id": "P10", "parameter": "glucose_rescue.FAILED_ACCESS_SHARE, delivered_share",
     "es": ("Vía fallida: de la glucosa en bolo por vía endovenosa o intraósea llega el 15 % hasta que se instala una "
            "vía nueva; la infusión al 10 %, el glucagón, el octreótido y la tiamina endovenosos pasan enteros por "
            "ella (el alcance de la decisión 8)."),
     "review": "pending",
     "review_es": ("El 15 % y el alcance se implementaron con la decisión 8 (docs/DECISIONES_3_4_8_MAGNITUDES.md); "
                   "la magnitud no tiene revisión registrada y el alcance es la decisión pendiente DC4.")},
    {"id": "P11", "parameter": "family_engine._discharge_alarm, DISCHARGE_RETURN_DELAY_MIN",
     "es": "Tras un alta, una glucosa bajo 60 hace que el paciente vuelva 20 minutos después.",
     "review": "pending",
     "review_es": ("El principio es de las decisiones docentes 1 y 2 del 2026-09-21 (un alta con el problema en curso "
                   "trae de vuelta al paciente); el umbral de 60 mg/dL y los 20 minutos no tienen revisión registrada.")},
    {"id": "P12", "parameter": "decisión docente 8 (2026-09-21)",
     "es": "La tiamina no despierta al paciente ni su ausencia lo deteriora.",
     "review": "decided", "review_es": "Decisión docente 8 (2026-09-21); no tiene magnitudes propias."},
)


# --- the three bank cases, as their narratives were authored -------------------
# Everything below reproduces clinical_cases exactly for hypoglycemia_28m and
# hypoglycemia_76f. hypoglycemia_54m_thiamine carries the corrections the
# faculty asked for on 2026-09-25 (its management focus contradicted decision
# 8); they are listed in the corrections registry.
_TEMPLATES = {
    "insulin": {
        "id": "hypoglycemia_28m",
        "axes": {"mechanism": "insulin", "iv_access": "working", "severity": "severe"},
        "conditions": {"sulfonylurea_effect": False, "endogenous_insulin": False, "glycogen_depleted": False,
                       "thiamine_deficient": False, "iv_access_failed": False, "diabetes": "type_1",
                       "arrival_glucose": 34, "arrival_mental_status": "Drowsy"},
        "assumptions": [
            {"condition": "diabetes", "es": "Diabetes tipo 1, confirmada por su información de emergencia."},
            {"condition": "glycogen_depleted", "es": "Reservas de glucógeno no agotadas: estaba bien al empezar "
                                                      "el turno y sólo omitió el almuerzo."},
            {"condition": "thiamine_deficient", "es": "Sin déficit de tiamina: ninguna exposición al alcohol ni ayuno."},
        ],
        "narrative": {
            "patient": {"age": 28, "sex": "male", "comorbidities": ["type 1 diabetes"]},
            "presentation": "A 28-year-old man is brought from work after becoming confused and having difficulty answering simple questions.",
            "history": {
                "chief": "His coworker reports sudden confusion and difficulty finding words.",
                "symptoms": ["His coworker noticed shaking and sweating before he became confused.",
                             "There was no witnessed seizure, fall or head injury."],
                "medical": "His coworker reports type 1 diabetes; his emergency information confirms this.",
                "medications": "His medication record lists basal and mealtime insulin.",
                "onset": "He was well at the start of work and became confused over the last 20 minutes.",
                "risks": "His coworker reports that he took his usual mealtime insulin but was called away before eating lunch.",
                "focused": {
                    "oral_intake": "His lunch was left uneaten after he took his mealtime insulin.",
                    "exposure": "His coworker reports no known alcohol or sedative exposure during the shift.",
                    "neurological_symptoms": "He became confused and had difficulty speaking; no one saw a persistent one-sided weakness.",
                },
            },
            "history_source": "Coworker and emergency medication information",
            "examination": {
                "Cardiac": "Regular tachycardia with palpable peripheral pulses.",
                "Respiratory": "Normal effort; clear bilateral breath sounds.",
                "Abdomen": "Soft and non-tender.",
                "Neurological": "Drowsy and confused, but opens eyes to voice; speech is slow and all limbs move symmetrically. Pupils are equal and reactive.",
            },
            "observable": {"sbp": 128, "dbp": 76, "hr": 112, "spo2": 98, "rr": 20, "temperature": 36.7},
            "investigations": {"lactate": 1.7, "hemoglobin": 14.8, "wbc": 8.2, "creatinine": .9,
                               "abg": (7.41, 39, 96), "vbg": (7.37, 46), "pocus": 0,
                               "chest_xray": "No acute pulmonary abnormality.", "troponin": 6},
            "faculty": {
                "diagnosis": "Severe insulin-associated hypoglycemia with neuroglycopenia",
                "findings": ["Low bedside glucose", "Autonomic symptoms before confusion", "Insulin-meal mismatch"],
                "focus": "Correct the reversible metabolic threat and verify neurological and glucose recovery.",
                "questions": ["Which bedside check could change immediate management?",
                              "Did the neurological findings resolve with correction?"],
            },
            "visual": {"skin": "mild pallor", "sweating": "marked"},
        },
    },
    "sulfonylurea": {
        "id": "hypoglycemia_76f",
        "axes": {"mechanism": "sulfonylurea", "iv_access": "working", "severity": "severe"},
        "conditions": {"sulfonylurea_effect": True, "endogenous_insulin": True, "glycogen_depleted": False,
                       "thiamine_deficient": False, "iv_access_failed": False, "diabetes": "type_2",
                       "arrival_glucose": 38, "arrival_mental_status": "Obtunded"},
        "assumptions": [
            {"condition": "diabetes", "es": "Diabetes tipo 2 tratada con glimepirida."},
            {"condition": "glycogen_depleted", "es": "Reservas de glucógeno no agotadas pese a dos días de ingesta "
                                                      "escasa (supuesto de esta configuración)."},
            {"condition": "narrative", "es": "La enfermedad renal crónica está en el relato y no en el motor: la "
                                              "recurrencia la modela sólo el efecto de la sulfonilurea."},
        ],
        "narrative": {
            "patient": {"age": 76, "sex": "female", "comorbidities": ["type 2 diabetes", "chronic kidney disease"]},
            "presentation": "A 76-year-old woman is brought by her son because she has become difficult to wake this morning.",
            "history": {
                "chief": "Her son reports that she has become unusually difficult to wake.",
                "symptoms": ["Her son noticed sweating and reduced interaction.",
                             "There was no witnessed seizure or head injury."],
                "medical": "Her son reports type 2 diabetes and chronic kidney disease; she is normally alert and independent at home.",
                "medications": "Her medication list includes glimepiride; she continued taking it despite eating very little.",
                "onset": "Her intake has been poor for two days; she was markedly less responsive this morning.",
                "risks": "She has continued a sulfonylurea during poor intake and has impaired renal function.",
                "focused": {
                    "oral_intake": "Her son reports that she has eaten little for two days but continued her usual tablets.",
                    "exposure": "Her son reports no new sedatives or known alcohol ingestion.",
                    "neurological_symptoms": "Her son describes a generalized reduction in responsiveness rather than a witnessed focal weakness.",
                },
            },
            "history_source": "Son and medication list",
            "examination": {
                "Cardiac": "Regular pulse with preserved peripheral volume.",
                "Respiratory": "Normal effort and clear bilateral breath sounds.",
                "Abdomen": "Soft without focal tenderness.",
                "Neurological": "Opens eyes only briefly to a firm stimulus and localizes with both arms. Pupils are equal and reactive.",
            },
            "observable": {"sbp": 134, "dbp": 78, "hr": 96, "spo2": 97, "rr": 18, "temperature": 36.5},
            "investigations": {"lactate": 1.8, "hemoglobin": 11.8, "wbc": 8.6, "creatinine": 2.1, "bun": 36,
                               "abg": (7.39, 40, 91), "vbg": (7.35, 47), "pocus": 1,
                               "chest_xray": "No focal consolidation or edema.", "troponin": 12},
            "faculty": {
                "diagnosis": "Sulfonylurea-associated hypoglycemia with recurrence risk",
                "findings": ["Low bedside glucose", "Continued sulfonylurea with reduced intake", "Impaired renal function"],
                "focus": "Correct glucose, reassess consciousness and plan continued monitoring for recurrent hypoglycemia.",
                "questions": ["Did an initial recovery establish that the cause had ended?",
                              "What informed your monitoring and specialist-support plan?"],
            },
            "visual": {"skin": "mild pallor", "sweating": "mild"},
        },
        # A composition that makes this patient drowsy rather than obtunded has
        # to say so wherever the case says how hard she is to wake.
        "moderate": {
            "presentation": "A 76-year-old woman is brought by her son because she has been drowsy and slow to answer this morning.",
            "chief": "Her son reports that she has been unusually drowsy and slow to answer.",
            "onset": "Her intake has been poor for two days; this morning she was drowsier and slower to answer than usual.",
            "Neurological": "Drowsy; opens her eyes to voice, answers simple questions slowly and moves all limbs symmetrically. Pupils are equal and reactive.",
        },
    },
    "alcohol_fasting": {
        "id": "hypoglycemia_54m_thiamine",
        "axes": {"mechanism": "alcohol_fasting", "iv_access": "failed", "severity": "severe"},
        "conditions": {"sulfonylurea_effect": False, "endogenous_insulin": True, "glycogen_depleted": True,
                       "thiamine_deficient": True, "iv_access_failed": True, "diabetes": "none",
                       "arrival_glucose": 32, "arrival_mental_status": "Drowsy"},
        "assumptions": [
            {"condition": "diabetes", "es": "Sin diabetes: su páncreas responde a una sobrecorrección."},
            {"condition": "thiamine_deficient", "es": "Déficit probable de tiamina en este paciente (supuesto de "
                                                       "esta configuración, no una regla del alcohol)."},
            {"condition": "iv_access_failed", "es": "La vía con que llega no está en la vena; no se ve antes de "
                                                     "usarla (pendiente de decisión docente)."},
        ],
        "narrative": {
            "patient": {"age": 54, "sex": "male", "comorbidities": ["alcohol use disorder", "poor oral intake"]},
            "presentation": "A 54-year-old man is brought from a shelter after being found drowsy and unsteady. He has eaten almost nothing for days.",
            "history": {
                "chief": "His speech is muddled and he says he feels shaky.",
                "symptoms": ["He has been unsteady on his feet.", "He has had no fever, cough or vomiting."],
                "medical": "He drinks heavily every day and has eaten very little for a week; he is not diabetic.",
                "medications": "He takes no regular medicines and has received no vitamins.",
                "onset": "The confusion and unsteadiness came on through this morning.",
                "risks": "He drinks heavily and has eaten almost nothing for days.",
                "focused": {
                    "oral_intake": "He has had almost nothing to eat for about a week, and alcohol most days.",
                    "neurological_symptoms": "His walking has been unsteady and he says his vision feels unfocused.",
                    "chest_pain": "He reports no chest pain.",
                },
            },
            "history_source": "Shelter staff and the paramedic record",
            "examination": {
                "Cardiac": "Regular mildly rapid pulse; no murmur.",
                "Respiratory": "Normal effort; clear breath sounds.",
                "Abdomen": "Soft, without tenderness or organomegaly.",
                "Neurological": "Drowsy but rousable; gaze is unsteady with a few beats of nystagmus, and gait could not be tested safely. Pupils are equal and reactive.",
            },
            "observable": {"sbp": 118, "dbp": 70, "hr": 104, "spo2": 97, "rr": 18, "temperature": 36.2,
                           "crt": 3, "extremities": "Cool"},
            "investigations": {"lactate": 2.4, "hemoglobin": 12.9, "wbc": 6.2, "creatinine": .8,
                               "abg": (7.44, 36, 92), "vbg": (7.40, 42), "pocus": 0,
                               "chest_xray": "No focal consolidation.", "troponin": 9, "potassium": 3.4},
            "faculty": {
                "diagnosis": "Hypoglycemia in a thiamine-depleted patient, at risk of Wernicke encephalopathy",
                "findings": ["Neuroglycopenia with a capillary glucose of {glucose} mg/dL",
                             "Weeks of alcohol use with almost no food: depleted thiamine",
                             "Unsteady gaze and nystagmus, which glucose alone will not correct"],
                # Corrected 2026-09-25: "Correct the glucose without precipitating an
                # encephalopathy" contradicted faculty decision 8.
                "focus": "Recognise and correct the hypoglycemia first, and check that the glucose actually rose. "
                         "Thiamine, for the deficiency his drinking and fasting make likely, is a second objective.",
                "questions": ["What did the gaze findings add to the glucose result?",
                              "Which findings made thiamine part of the plan, and when did it belong?"],
            },
            "visual": {"skin": "mild pallor", "sweating": "mild"},
        },
    },
}
BANK_ORDER = ("insulin", "sulfonylurea", "alcohol_fasting")

# What a failed line adds to what the faculty reads about a case, whichever
# mechanism it comes with. hypoglycemia_54m_thiamine carries it since 2026-09-25.
_FAILED_LINE = {
    "finding": "The glucose barely rises after an intravenous dextrose bolus: the line is not in the vein",
    "focus": "When the glucose does not rise, look at the line and at what actually reached the patient.",
    "question": "When the glucose did not rise as expected, what did you check?",
}

# --- evaluation: the declaration inputs of each mechanism -----------------------
# For hypoglycemia_28m and hypoglycemia_76f these are the texts
# case_assessment_bank carried before 2026-09-25, unchanged.
_ASSESSMENT = {
    "insulin": {
        "d1_text": "The glucose is low enough to explain the altered state and the correction is time-critical.",
        "d3_text": "Intravenous dextrose is executable, and vascular access may have to be established first.",
        "d3_expected": ["Gives dextrose", "secures the route it needs"],
        "d3_alternatives": ["Glucagon when access is not available", "oral carbohydrate once the patient is alert"],
        "d3_actions": ("dextrose", "vascular_access", "glucagon", "oral_carbohydrate"),
        "d5_text": ("Once the glucose and the consciousness recover, the decision is whether this patient can "
                    "safely leave and what would bring them back."),
        "d5_expected": ["Decides the destination on the recovery observed", "states what is still pending"],
        "d5_alternatives": ["Keeping the patient for a stated period before deciding"],
        "events": (),
    },
    "sulfonylurea": {
        "d1_text": ("The glucose is low and the agent that caused it is long-acting: correction is urgent and "
                    "the recurrence is the reason the encounter continues."),
        "d3_text": "Dextrose corrects it; the recurrence risk is what the rest of the management addresses.",
        "d3_expected": ["Gives dextrose", "plans for the recurrence the agent carries"],
        "d3_alternatives": ["A dextrose infusion rather than repeated boluses", "octreotide stated for a sulfonylurea"],
        "d3_actions": ("dextrose", "dextrose_infusion", "vascular_access", "octreotide", "oral_carbohydrate"),
        "d5_text": ("A sulfonylurea patient who recovers is not a patient who can leave: the decision is "
                    "observation and its length."),
        "d5_expected": ["Arranges continued observation rather than discharge",
                        "states what is watched and for how long"],
        "d5_alternatives": ["Admission stated as the observation"],
        "events": ("hypo_unsafe_discharge",),
    },
    # New version, 2026-09-25: glucose first; thiamine a second objective and no
    # longer a critical event (it was one, hypo_no_thiamine, until then).
    "alcohol_fasting": {
        "d1_text": ("The glucose is low enough to explain the altered state and its correction comes first. The "
                    "drinking and the week without food make a thiamine deficiency likely: a second priority, "
                    "not the first."),
        "d3_text": "Dextrose is executable; glucagon mobilises little in a patient whose glycogen is spent.",
        "d3_expected": ["Gives dextrose"],
        "d3_alternatives": ["Glucagon by another route, knowing that little glycogen is left"],
        "d3_actions": ("dextrose", "vascular_access", "glucagon"),
        "d5_text": ("The decision is where the correction continues, with the reason he became hypoglycemic "
                    "addressed and thiamine in the plan, not only the number."),
        "d5_expected": ["Decides the destination with the cause in it", "states what continues"],
        "d5_alternatives": ["Admission stated as the continuation"],
        "events": (),
    },
}
_THIAMINE_SECONDARY = {
    "d3_text": (" Thiamine is executable and belongs to the plan as a second objective: its omission alone "
                "does not make the correction of the glucose inadequate, and it is never a reason to delay it."),
    "d3_expected": "adds thiamine, as a second objective",
    "d3_alternative": "thiamine before, with or after the dextrose",
    "d3_action": "thiamine",
}
_FAILED_LINE_ASSESSMENT = {
    "d3_text": (" The line the patient arrives with is not in the vein: a dextrose bolus given through it does "
                "not reach the patient until a new line is placed."),
    "d3_expected": "gets it into the patient by a route that works",
    "d3_action": "vascular_access",
    # An opportunity of the domain that checks delivery and response. Not a
    # critical event (faculty, 2026-09-25).
    "d4": {"opportunity": ("The glucose does not rise as expected after an intravenous dextrose bolus: the line "
                           "is not in the vein, and the engine reports it when a bolus is given through it. What "
                           "this case asks is to check the delivery, not only the number."),
           "expected": ["Rechecks the glucose after the dose",
                        "recognises that the dose did not reach the patient and restores a route that does"],
           "alternatives": ["Placing a new line before the first dose, which avoids the failure",
                            "rechecking the mental state rather than the number"],
           "window": (5, 60), "actions": ("reassessment", "vascular_access", "glucagon"),
           "studies": ("poc_glucose",)},
}
_MODERATE_D1 = (" At arrival the glucose is above the engine's seizure threshold: its correction is still the "
                "priority, with some more time before the brain pays for the delay.")


def _key(configuration):
    axes = configuration["axes"]
    return axes["mechanism"], axes["iv_access"], axes["severity"]


def _compose(mechanism, access, severity):
    """One configuration from the bank case of its mechanism, changing only what the axes require."""
    template = _TEMPLATES[mechanism]
    configuration = {"family": FAMILY, "catalog_version": VERSION,
                     "axes": {"mechanism": mechanism, "iv_access": access, "severity": severity},
                     "conditions": deepcopy(template["conditions"]),
                     "assumptions": deepcopy(template["assumptions"]),
                     "narrative": deepcopy(template["narrative"]),
                     "derived_from": template["id"]}
    if (mechanism, access, severity) == _key(template):
        return {**configuration, "id": template["id"], "origin": "bank"}
    configuration["origin"] = "composition"
    configuration["id"] = f"{FAMILY}_cfg_{mechanism}_{access}_{severity}"
    configuration["conditions"]["iv_access_failed"] = access == "failed"
    configuration["assumptions"] = [item for item in configuration["assumptions"]
                                    if item["condition"] != "iv_access_failed"]
    if access == "failed":
        configuration["assumptions"].append(
            {"condition": "iv_access_failed", "es": "La vía con que llega no está en la vena; no se ve antes de "
                                                     "usarla (pendiente de decisión docente)."})
    if severity != template["axes"]["severity"]:
        if severity == "moderate":
            configuration["conditions"]["arrival_glucose"] = MODERATE_ARRIVAL_GLUCOSE
            configuration["conditions"]["arrival_mental_status"] = "Drowsy"
            narrative = configuration["narrative"]
            for field, text in template.get("moderate", {}).items():
                if field == "presentation":
                    narrative["presentation"] = text
                elif field in ("chief", "onset"):
                    narrative["history"][field] = text
                else:
                    narrative["examination"][field] = text
        else:
            raise case_catalog.CatalogError("Every bank template is severe; a severe composition keeps its glucose.")
    return configuration


def _all():
    ordered = [_compose(*_key(_TEMPLATES[mechanism])) for mechanism in BANK_ORDER]
    for mechanism in AXES["mechanism"]["values"]:
        for access in AXES["iv_access"]["values"]:
            for severity in AXES["severity"]["values"]:
                if (mechanism, access, severity) not in {_key(c) for c in ordered}:
                    ordered.append(_compose(mechanism, access, severity))
    return ordered


_CONFIGURATIONS = _all()
_BY_ID = {configuration["id"]: configuration for configuration in _CONFIGURATIONS}


def configurations():
    """All twelve combinations, bank cases first in the bank's order."""
    return [deepcopy(configuration) for configuration in _CONFIGURATIONS]


def bank_configurations():
    return [deepcopy(c) for c in _CONFIGURATIONS if c["origin"] == "bank"]


def review_candidates():
    """The compositions: faculty sandbox only, never a resident's usual selection."""
    return [deepcopy(c) for c in _CONFIGURATIONS if c["origin"] != "bank"]


def configuration(configuration_id):
    try:
        return deepcopy(_BY_ID[configuration_id])
    except KeyError:
        raise case_catalog.CatalogError(f"Unknown hypoglycemia configuration: {configuration_id}") from None


def is_review_candidate(configuration_id):
    found = _BY_ID.get(configuration_id)
    return found is not None and found["origin"] != "bank"


def faculty_fields(configuration):
    """The faculty block, composed from the mechanism and a failed line."""
    base = configuration["narrative"]["faculty"]
    glucose = configuration["conditions"]["arrival_glucose"]
    findings = [text.format(glucose=glucose) for text in base["findings"]]
    focus, questions = base["focus"], list(base["questions"])
    if configuration["conditions"]["iv_access_failed"]:
        findings.append(_FAILED_LINE["finding"])
        focus = focus + " " + _FAILED_LINE["focus"]
        questions.append(_FAILED_LINE["question"])
    return {"diagnosis": base["diagnosis"], "findings": findings, "focus": focus, "questions": questions}


def definitive_actions(configuration):
    return ["dextrose", *(["thiamine"] if configuration["conditions"]["thiamine_deficient"] else []),
            "reassessment"]


def case_arguments(configuration):
    """Everything clinical_cases needs to build this case, and nothing it has to decide."""
    narrative, conditions = configuration["narrative"], configuration["conditions"]
    faculty = faculty_fields(configuration)
    return {
        "identifier": configuration["id"],
        "patient": deepcopy(narrative["patient"]),
        "presentation": narrative["presentation"],
        "history": deepcopy(narrative["history"]),
        "history_source": narrative["history_source"],
        "examination": deepcopy(narrative["examination"]),
        "observable": {**deepcopy(narrative["observable"]), "mental": conditions["arrival_mental_status"],
                       "glucose": conditions["arrival_glucose"]},
        "investigations": deepcopy(narrative["investigations"]),
        "diagnosis": faculty["diagnosis"], "findings": faculty["findings"],
        "focus": faculty["focus"], "questions": faculty["questions"],
        "actions": definitive_actions(configuration),
        "visual": deepcopy(narrative["visual"]),
        "flags": {"recurrence": conditions["sulfonylurea_effect"],
                  "endogenous_insulin": conditions["endogenous_insulin"],
                  "thiamine_deficient": conditions["thiamine_deficient"],
                  "iv_access_failed": conditions["iv_access_failed"],
                  "glycogen_depleted": conditions["glycogen_depleted"]},
    }


def declaration_inputs(configuration):
    """What case_assessment_bank._hypo needs for this configuration, derived here and nowhere else."""
    mechanism = configuration["axes"]["mechanism"]
    block = deepcopy(_ASSESSMENT[mechanism])
    d1 = block["d1_text"] + (_MODERATE_D1 if configuration["axes"]["severity"] == "moderate" else "")
    d3_text, expected = block["d3_text"], list(block["d3_expected"])
    alternatives, actions = list(block["d3_alternatives"]), list(block["d3_actions"])
    d4 = None
    if configuration["conditions"]["iv_access_failed"]:
        d3_text += _FAILED_LINE_ASSESSMENT["d3_text"]
        expected.append(_FAILED_LINE_ASSESSMENT["d3_expected"])
        if _FAILED_LINE_ASSESSMENT["d3_action"] not in actions:
            actions.append(_FAILED_LINE_ASSESSMENT["d3_action"])
        d4 = deepcopy(_FAILED_LINE_ASSESSMENT["d4"])
    if configuration["conditions"]["thiamine_deficient"]:
        d3_text += _THIAMINE_SECONDARY["d3_text"]
        expected.append(_THIAMINE_SECONDARY["d3_expected"])
        alternatives.append(_THIAMINE_SECONDARY["d3_alternative"])
        if _THIAMINE_SECONDARY["d3_action"] not in actions:
            actions.append(_THIAMINE_SECONDARY["d3_action"])
    return {"case_id": configuration["id"], "d1_text": d1, "d3_text": d3_text, "d3_expected": expected,
            "d3_alternatives": alternatives, "d3_actions": tuple(actions),
            "d5_text": block["d5_text"], "d5_expected": list(block["d5_expected"]),
            "d5_alternatives": list(block["d5_alternatives"]), "d4": d4, "events": tuple(block["events"])}


def check(configuration):
    return case_catalog.check(__import__(__name__), configuration)


def signature(configuration):
    return case_catalog.signature(__import__(__name__), configuration)


def fingerprint_components(configuration):
    """What a clinical review of this configuration is a review of."""
    import family_engine
    from case_assessment_bank import declaration_for
    rules = [{"id": r["id"], "kind": r["kind"], "es": r["es"],
              "logic": case_catalog.logic_of(r["check"]) if r["check"] else None} for r in RELATIONS]
    functions = [value for name, value in sorted(vars(glucose_rescue).items())
                 if callable(value) and getattr(value, "__module__", None) == glucose_rescue.__name__]
    parameters = {"glucose_rescue": case_catalog.constants_of(glucose_rescue),
                  "logic": {f.__name__: case_catalog.logic_of(f) for f in functions},
                  "discharge": {"delay_min": family_engine.DISCHARGE_RETURN_DELAY_MIN,
                                "alarm": case_catalog.logic_of(family_engine._discharge_alarm)},
                  "moderate_arrival_glucose": MODERATE_ARRIVAL_GLUCOSE,
                  "simplifications": [dict(item) for item in SIMPLIFICATIONS]}
    history = configuration["narrative"]["history"]
    cues = {"medications": history["medications"], "medical": history["medical"], "risks": history["risks"],
            "oral_intake": history["focused"].get("oral_intake"),
            "failed_line": [glucose_rescue.FAILED_ACCESS_TEXT, glucose_rescue.NEW_ACCESS_TEXT]
            if configuration["conditions"]["iv_access_failed"] else None}
    return {"conditions": {"axes": configuration["axes"], "conditions": configuration["conditions"],
                           "assumptions": configuration["assumptions"]},
            "rules": rules, "parameters": parameters, "cues": cues,
            "narrative": {**case_arguments(configuration), "flags": None},
            "assessment": case_catalog.plain(declaration_for(configuration))}


def fingerprint(configuration):
    return case_catalog.fingerprint(__import__(__name__), configuration)


# --- compatible: the concrete checks behind the word ---------------------------
_REQUIRED_CASE = {"id", "patient", "presentation", "history", "history_source", "examination", "observable",
                  "ecg_profile", "investigations", "visual_profile", "engine", "faculty"}
_REQUIRED_HISTORY = {"chief_complaint", "associated_symptoms", "medical_history", "medications", "allergies",
                     "onset", "risk_factors"}
_REQUIRED_OBSERVABLE = {"sbp", "dbp", "hr", "spo2", "respiratory_rate", "work_of_breathing", "crt", "extremities",
                        "mental_status", "rhythm", "pulse_present", "temperature_c", "glucose_mg_dl",
                        "peripheral_perfusion"}


def contract_problems(case):
    """The bank's own contract (test_clinical_cases), applied to one built case."""
    from clinical_cases import INVESTIGATION_IDS
    from ecg12 import RHYTHMS
    from visual_observations import visual_observations
    problems = []

    def need(condition, message):
        if not condition:
            problems.append(message)

    need(_REQUIRED_CASE <= set(case), "missing case fields: " + ", ".join(sorted(_REQUIRED_CASE - set(case))))
    if problems:
        return problems
    history, o, studies = case["history"], case["observable"], case["investigations"]
    need(case["engine"]["family"] == FAMILY, "the engine family is not hypoglycemia")
    need(_REQUIRED_HISTORY <= set(history), "missing history topics")
    need(len(case["presentation"].split()) <= 70, "the arrival presentation is longer than 70 words")
    need(len(history["chief_complaint"]) <= 2, "the chief complaint has more than two sentences")
    need(all(isinstance(v, list) and v and all(isinstance(s, str) and s.strip() for s in v)
             for v in history.values()), "a history topic is empty")
    need({"Cardiac", "Respiratory", "Abdomen", "Neurological"} <= set(case["examination"]),
         "an examination area is missing")
    need(case["faculty"]["discriminating_findings"] and case["faculty"]["sources"], "faculty fields are incomplete")
    need(_REQUIRED_OBSERVABLE <= set(o), "missing arrival observables")
    need(o["sbp"] > o["dbp"] and o["hr"] > 0 and o["pulse_present"], "the arrival circulation is not coherent")
    need(o["rhythm"].lower() in RHYTHMS, "the arrival rhythm is not one the ECG can draw")
    need(o["glucose_mg_dl"] == studies["poc_glucose"]["result"]["glucose_mg_dl"]
         == studies["basic_labs"]["result"]["glucose_mg_dl"], "the arrival glucose and its studies disagree")
    need(o["temperature_c"] == studies["temperature"]["result"]["temperature_c"],
         "the arrival temperature and its study disagree")
    need(case["engine"]["baseline_lactate"] == studies["lactate"]["result"]["lactate_mmol_l"],
         "the lactate and the engine baseline disagree")
    need(set(studies) <= set(INVESTIGATION_IDS), "a study is not one the bank can carry")
    need("pending" in studies["blood_cultures"]["result"]["report"].lower(), "blood cultures are not pending")
    need(case["faculty"]["diagnosis"].lower() not in case["presentation"].lower(),
         "the arrival presentation names the diagnosis")
    need(o["glucose_mg_dl"] < 54 and o["mental_status"] in {"Drowsy", "Obtunded"}
         and o["peripheral_perfusion"] == "preserved", "the hypoglycemia discriminators are not met")
    if o["mental_status"] != "Alert":
        need(case["history_source"] != "Patient"
             and history["chief_complaint"][0].startswith(("His ", "Her ")),
             "a patient who is not alert needs a collateral history")
    visible = visual_observations({"observable": o, "encounter_spec": {"visual_profile": case["visual_profile"]}})
    need(visible["mental_status"] == o["mental_status"].lower() and visible["diaphoresis"] in {"mild", "marked"}
         and visible["skin_color"] != "not recorded" and visible["expression"] != "neutral",
         "the picture contradicts the arrival state")
    return problems


def compatibility(configuration):
    """'Compatible', as the list of checks that establish it, each with its result."""
    import case_assessment
    import catalog_trajectories
    from clinical_cases import variant_by_id
    checks = []
    findings = check(configuration)
    checks.append({"id": "relations", "passed": not findings,
                   "es": "Relaciones del catálogo (necesarias y simplificaciones)",
                   "detail": [f["message"] for f in findings]})
    try:
        case = variant_by_id(configuration["id"])
    except KeyError as error:
        checks.append({"id": "built", "passed": False, "es": "El caso se construye", "detail": [str(error)]})
        return {"compatible": False, "checks": checks}
    problems = contract_problems(case)
    checks.append({"id": "case_contract", "passed": not problems,
                   "es": "Contrato de los casos del banco (signos, estudios, fuente, imagen)", "detail": problems})
    problems = case_assessment.verify(case["id"])
    checks.append({"id": "declaration_reachable", "passed": not problems,
                   "es": "Declaraciones de evaluación alcanzables en el caso", "detail": problems})
    try:
        state = catalog_trajectories.launch(configuration["id"], FAMILY, allow_review_candidates=True)
        launched = state["engine_family"] == FAMILY and state["observable"]["glucose_mg_dl"] == \
            configuration["conditions"]["arrival_glucose"]
        detail = [] if launched else ["the launched state does not carry the configuration"]
    except (ValueError, KeyError) as error:
        launched, detail = False, [str(error)]
    checks.append({"id": "engine_launch", "passed": launched, "es": "Se lanza en el motor real", "detail": detail})
    return {"compatible": all(item["passed"] for item in checks), "checks": checks}


def reference(case_id):
    """Which catalogue configuration a case is, for the records that launch it; None if none."""
    found = _BY_ID.get(case_id)
    if found is None:
        return None
    return {"family": FAMILY, "version": VERSION, "configuration_id": found["id"], "origin": found["origin"],
            "axes": dict(found["axes"]), "signature": signature(found)["id"],
            "fingerprint": current_fingerprint(found["id"])}


# The code does not change inside a running process, so neither do these.
from functools import lru_cache as _lru_cache


# Kept apart: the compatibility launches the engine, and a launch reads the
# fingerprint (reference), so one cache for both would call itself.
@_lru_cache(maxsize=None)
def _current_fingerprint(configuration_id):
    return fingerprint(_BY_ID[configuration_id])


@_lru_cache(maxsize=None)
def _current_compatibility(configuration_id):
    return compatibility(_BY_ID[configuration_id])


def current_fingerprint(configuration_id):
    return deepcopy(_current_fingerprint(configuration_id))


def current_compatibility(configuration_id):
    return deepcopy(_current_compatibility(configuration_id))
