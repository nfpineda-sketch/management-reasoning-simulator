"""Small, deterministic order interpreter for the independent case families.

The parser identifies orders; the family engine validates whether they can be
executed.  It does not infer doses, routes, clinical reasoning, or treatment from
a diagnosis/expected effect.  Unrecognized explicit orders remain visible as
clarifications instead of being reported as successful interventions.
"""
from __future__ import annotations

import re
import unicodedata

from shared_order_quantities import parse_volume_ml
from shared_order_language import _normalize, _route, _amount


NEW_TREATMENT_ACTIONS = frozenset({
    "fluid", "oxygen", "niv", "nitroglycerin", "antibiotics", "bronchodilator",
    "beta_blocker", "diltiazem", "amiodarone", "procedural_sedation", "cardioversion", "ventilator_adjustment", "steroid", "dextrose", "naloxone", "blood", "ppi", "aspirin", "p2y12", "nitroglycerin_bolus",
    "anticoagulation", "bag_mask", "intubation", "norepinephrine", "dobutamine", "diuretic",
    "magnesium", "epinephrine", "epinephrine_bolus", "epinephrine_im", "continuous_bronchodilator",
    "ventilator_disconnect", "chest_decompression", "thrombolysis", "stress_test",
    "hemorrhage_control", "pelvic_binder", "tranexamic_acid", "result_review",
    "octreotide", "glucagon", "calcium", "thiamine", "oral_carbohydrate", "dextrose_infusion", "naloxone_infusion",
    "atropine", "transcutaneous_pacing", "opioid_analgesia",
    "neuromuscular_blockade", "sedation_infusion",
    "vascular_access", "monitoring", "npo", "urinary_catheter", "gastric_tube", "antipyretic",
})

# A continuous nebulization without a stated rate runs at the usual 10 mg/h.
CONTINUOUS_NEBULIZER_MG_PER_H = 10.0

_AGENTS = {
    "antibiotics": {
        "ceftriaxone": r"ceftriaxon[ae]", "azithromycin": r"azithromycin|azitromicina",
        "piperacillin-tazobactam": r"piperacillin[- /]+tazobactam|piperacilina[- /]+tazobactam|zosyn",
        "vancomycin": r"vancomycin|vancomicina",
    },
    "bronchodilator": {"albuterol": r"albuterol|salbutamol", "ipratropium": r"ipratropium|ipratropio"},
    "steroid": {
        "prednisone": r"prednisone|prednisona", "methylprednisolone": r"methylprednisolone|metilprednisolona",
        "hydrocortisone": r"hydrocortisone|hidrocortisona", "dexamethasone": r"dexamethasone|dexametasona",
    },
    "dextrose": {"dextrose": r"dextrose|dextrosa|glucosa(?:\s+intravenosa)?|d50|d10"},
    "magnesium": {"magnesium sulfate": r"magnesium(?:\s+sulfate)?|sulfato\s+de\s+magnesio|magnesio|mgso4|mg\s*so4"},
    "thrombolysis": {"tenecteplase": r"tenecteplase|tenecteplasa|tnk", "alteplase": r"alteplase|alteplasa|rt-?pa|\btpa\b",
                     "streptokinase": r"streptokinase|estreptoquinasa"},
    "octreotide": {"octreotide": r"octreotide|octre[oó]tido|octreotida"},
    "glucagon": {"glucagon": r"glucagon|glucag[oó]n"},
    # The membrane stabiliser of a calcium-channel blockade and of a severe
    # hyperkalaemia, added with the bradycardia family (2026-09-23). The two
    # salts are not interchangeable in strength and the engine keeps which one.
    "calcium": {
        "calcium gluconate": r"(?:gluconato\s+de\s+)?calcio\s+gluconato|calcium\s+gluconate|"
                             r"gluconato\s+de\s+calcio",
        "calcium chloride": r"cloruro\s+de\s+calcio|calcium\s+chloride",
    },
    "thiamine": {"thiamine": r"thiamine|tiamina|vitamin b1|vitamina b1"},
    "naloxone": {"naloxone": r"naloxone|naloxona|narcan"},
    "atropine": {"atropine": r"atropine|atropina"},
    # The ward's own analgesics and antipyretics (faculty decision 14, 2026-09-21).
    "antipyretic": {
        "paracetamol": r"paracetamol|acetaminophen|acetaminofen|tylenol|perfalgan",
        "ibuprofen": r"ibuprofen|ibuprofeno|caldolor",
        "ketorolac": r"ketorolac|ketorolaco|toradol",
        "metamizole": r"metamizol|dipirona|dipyrone|novalgina",
    },
    # Morphine is a treatment in every family, and a decision in some.
    "opioid_analgesia": {"morphine": r"morphine|morfina", "fentanyl": r"fentanyl|fentanilo"},
    "ppi": {"pantoprazole": r"pantoprazole|pantoprazol", "omeprazole": r"omeprazole|omeprazol"},
    "aspirin": {"aspirin": r"aspirin|aspirina|asa|aas"},
    # The second antiplatelet of a coronary syndrome. Aspirin is the first one
    # and stays; this is what is added to it (faculty decision, 2026-09-22).
    "p2y12": {"clopidogrel": r"clopidogrel|clopidrogrel|plavix",
              "ticagrelor": r"ticagrelor|brilinta|brilique",
              "prasugrel": r"prasugrel|effient"},
    "anticoagulation": {"heparin": r"heparin|heparina", "enoxaparin": r"enoxaparin|enoxaparina"},
    "beta_blocker": {"metoprolol": r"metoprolol", "propranolol": r"propranolol"},
    "diltiazem": {"diltiazem": r"diltiazem|dilt"},
    "amiodarone": {"amiodarone": r"amiodarone|amiodarona|amio"},
    "procedural_sedation": {
        "etomidate": r"etomidate|etomidato", "midazolam": r"midazolam",
        "ketamine": r"ketamine|ketamina", "propofol": r"propofol",
        "dexmedetomidine": r"dexmedetomidine|dexmedetomidina|precedex",
    },
    # The block is its own drug class: it takes movement, and neither
    # consciousness nor pain (faculty decision 11, 2026-09-21).
    "neuromuscular_blockade": {
        "rocuronium": r"rocuronium|rocuronio", "succinylcholine": r"succinylcholine|succinilcolina|suxamethonium",
        "vecuronium": r"vecuronium|vecuronio", "cisatracurium": r"cisatracurium|cisatracurio",
    },
    "diuretic": {"furosemide": r"furosemide|furosemida|lasix"},
}
CROSSMATCH = (r"crossmatch|cross[- ]match|type_and_screen|type and (?:screen|cross(?:match)?)|"
              r"blood typ(?:e|ing)|grupo_y_pruebas|grupo y (?:pruebas cruzadas|rh|factor(?: rh)?)|"
              r"grupo sanguineo|grupo y rh|pruebas cruzadas|pruebas de compatibilidad|"
              r"tipificacion(?: sanguinea)?|clasificacion (?:sanguinea|abo)|"
              r"reserv(?:a|ar|o|e)\w*\s+(?:de\s+)?(?:\d+\s+)?(?:(?:unidades?|u)\s+(?:de\s+)?)?"
              r"(?:sangre|globulos rojos|hematies|gr\b)")
_TRANSFUSING = re.compile(r"\b(?:transfund\w*|transfus\w*|pas(?:ar|o|e|a)|administr\w*|d(?:ar|oy|e)|give|"
                          r"start|inici\w*|instal\w*|infund\w*)\b")

_DIAGNOSTICS = {
    # How a head CT is asked for here, found missing on 2026-09-24: "TC de
    # craneo", "TAC cerebral", "tomografia computada de encefalo", "scanner".
    "head_ct": r"head ct|ct head|brain ct|ct brain|ct (?:scan )?of the (?:head|brain)|head ct scan|"
               r"(?:tac|tc|scanner|escaner|tomografia(?:\s+(?:axial\s+)?computa(?:da|rizada))?)"
               r"(?:\s+de)?\s+(?:cerebro|craneo|encefalo)|"
               r"(?:tac|tc|scanner|escaner|tomografia(?:\s+(?:axial\s+)?computa(?:da|rizada))?)\s+cerebral",
    "abdominal_ct": r"abdominal ct|ct abdomen|ct of the abdomen|tac(?:\s+de)?\s+abdomen|tc(?:\s+de)?\s+abdomen",
    # The blood bank's request, recognised on 2026-09-24 and modelled in no case
    # yet: it is recorded as asked for and answered with nothing invented. A
    # reservation of units is this request too, and never a transfusion.
    "crossmatch": CROSSMATCH,
    "cortisol": r"cortisol",
    "thyroid_function": r"thyroid function|thyroid tests|tsh|perfil tiroideo|funcion tiroidea",
    "ketones": r"ketones|beta[- ]hydroxybutyrate|cetonas|cetonemia|beta[- ]hidroxibutirato",
    "toxicology": r"toxicology|toxicology screen|toxicologia|screening toxicologico",
    # A qualified ultrasound is the study it names, not the emergency protocol:
    # "ecografia renal" used to return both (2026-09-23).
    "pocus": r"pocus|point[- ]of[- ]care ultrasound|bedside ultrasound|"
             r"ecograf[ií]a(?!\s*(?:renal|reno|de\s+(?:las?\s+)?v[ií]as?\s+urinarias?|"
             r"de\s+ri[nñ][oó]n))(?:\s+a pie de cama)?|"
             r"ultrasonido(?!\s*(?:renal|reno))",
    "lactate": r"lactate|lactato",
    "vbg": r"vbg|venous blood gases?|venous blood gas|gasometria venosa|gases venosos",
    "abg": r"abg|arterial blood gases?|arterial blood gas|gasometria arterial|gases arteriales",
    # Faculty decision 2026-09-21: the panels and analytes of this basic set are
    # all written many ways, in two languages. They resolve to the one panel the
    # cases carry; separate per-analyte panels are a later piece of work.
    "basic_labs": r"basic labs|blood tests|blood work|laboratory tests|lab work|labs|"
                  r"laboratorio|examenes de laboratorio|examenes generales|examenes de sangre|"
                  r"hemograma|cbc|bmp|cmp|chemistry panel|metabolic panel|panel metabolico|"
                  r"electrolytes|electrolitos(?:\s+plasmaticos)?|elp|"
                  r"creatinine|creatinina|funcion renal|renal function|pruebas renales|"
                  r"bun|urea|nitrogeno ureico|blood urea nitrogen|"
                  r"perfil bioquimico|perfil hepatico|pruebas hepaticas|liver (?:panel|function tests)|lfts",
    "temperature": r"temperature|temperatura|temp",
    "poc_glucose": r"poc glucose|blood glucose|blood sugar|fingerstick|finger stick|glucose|glucosa|glicemia|glucemia|hgt|hemoglucotest",
    "chest_xray": r"chest x[- ]?ray|chest radiograph|cxr|radiografia(?:\s+(?:de\s+)?torax)?|"
                  r"rx(?:\s+de)?(?:\s+torax)?|placa(?:\s+(?:de\s+)?torax)?|x[- ]?rays?|radiograph",
    "urinalysis": r"urinalysis|urine analysis|urine dip|orina completa|examen de orina",
    "blood_cultures": r"blood cultures?|hemocultivos?",
    # The first test of the embolism algorithm, and it did not exist: a request
    # for it held the whole submission as unreadable (played 2026-09-22).
    "d_dimer": r"d[- ]?dimer|dd[- ]?dimer|dimero[- ]?d|d[- ]?dimero|dimero|dimeros? d",
    # "Cardiac markers" and "cardiac enzymes" are how the request is spoken; in
    # this encounter the marker is the troponin, and the result says so.
    "troponin": r"troponin|troponina|marcadores? cardiacos?|enzimas cardiacas|"
                r"cardiac (?:markers?|enzymes)|biomarcadores? cardiacos?|curva de troponinas?",
    # "Angiotomografia de torax" is how the study is written here in full; only
    # its abbreviations were listed, so the written form was refused (2026-09-23).
    "ctpa": r"ctpa|ct pulmonary angiogra(?:phy|m)|pulmonary ct angiogra(?:phy|m)|angio(?:[- ]?tc|tac|tomografia)(?:\s+(?:de\s+)?(?:torax|pulmonar))?",
    # The two studies a trauma resident looks again with, after the chest is
    # drained and the patient is still unstable (faculty decision 2.4).
    "efast": r"e[- ]?fast|extended\s+fast|\bfast\b(?:\s+(?:exam|examen|scan))?|"
             r"eco(?:graf[ií]a)?\s+(?:fast|de\s+trauma)|trauma\s+ultrasound",
    "pelvis_xray": r"(?:radiograf[ií]a|rx|placa|x[- ]?ray)\s+(?:de\s+)?(?:la\s+)?pelvis|"
                   r"pelvi[cs]\s+(?:x[- ]?ray|radiograph|film)|rx\s+p[eé]lvi[sc]a?",
    # The study of the flank-pain family (2026-09-23). Matched before the plain
    # ultrasound words so that asking for "ecografia renal" never returns the
    # emergency POCUS protocol instead.
    "renal_ultrasound": r"(?:eco(?:graf[ií]a)?|ultrasoni?d[oe]|ultrasound|us)\s*"
                        r"(?:renal(?:es)?(?:\s+y\s+vesical)?|de\s+(?:las?\s+)?v[ií]as?\s+urinarias?|"
                        r"reno[- ]?vesical|vesico[- ]?renal|de\s+ri[nñ][oó]n(?:es)?|kidney|renal\s+tract)|"
                        r"(?:renal|urinary\s+tract)\s+ultrasound|pielo[- ]?tac|"
                        r"(?:tc|tac|ct)\s+(?:de\s+)?(?:abdomen\s+y\s+pelvis\s+)?sin\s+contraste\s+(?:renal|urinari[ao])|"
                        r"uro[- ]?(?:tc|tac|ct)|ct\s+(?:kub|urogram)|"
                        # "Eco renal y vesical" is one request; the clause
                        # splitter makes two, and the second was held as an
                        # unrecognized study (2026-09-23).
                        r"vesical|bladder\s+ultrasound",
    # The British spelling as well: the documents of this project are written
    # in it, so a resident reading "haemoglobin" there and typing it back was
    # refused while the Spanish "hemoglobina" was accepted (2026-09-23).
    "hemoglobin": r"h(?:a?e)moglobin|hemoglobina|hb",
    # Faculty decision 7 of 2026-09-21: these are studies of their own, and they
    # are matched before the plain twelve-lead so that asking for them never
    # returns a standard tracing instead.
    "ecg_right": r"deriva(?:das|ciones)\s+derechas|derechas\s+v[34]r|ecg\s+derecho|"
                 r"electrocardiograma\s+derecho|right[- ]sided (?:ecg|leads?)|right precordial leads?|"
                 r"v[34]r(?:\s*[-a]\s*v[34]r)?|v3r|v4r",
    "ecg_posterior": r"deriva(?:das|ciones)\s+posteriores|ecg\s+posterior|electrocardiograma\s+posterior|"
                     r"posterior (?:ecg|leads?)|v7\s*(?:[-,a]\s*)?v?8?\s*(?:[-,ay]\s*)?v?9|v7|v8|v9",
    "ecg": r"(?:12[- ](?:lead|derivadas?)\s+)?ecg(?:\s+(?:de\s+)?12\s+derivadas?)?|ekg|electrocardiogram|electrocardiograma",
}
# An airway/ventilation order and the settings fragments that may follow it.
# The infusions the engine runs. A resident who names one is not naming a role.
_SUPPORT_ORDERS = (
    # "VVP" is how a peripheral venous line is written on a Chilean chart; the
    # rehearsal of the twenty-scenario batch held two resuscitations for it
    # (2026-09-24).
    ("vascular_access", r"\bvias?\s+(?:venosas?|perifericas?|gruesas?|ev|iv)\b|\bvia\s+venosa\b|\bvvps?\b|"
                        r"\bacceso\s+(?:venoso|vascular)\b|\bbranula\b|\bcateter\s+venoso\b|"
                        r"\b(?:peripheral\s+)?(?:iv|intravenous)\s+(?:line|access|cannula)\b|\blarge[- ]bore\b"),
    ("urinary_catheter", r"\bsonda\s+(?:foley|vesical|urinaria)\b|\bfoley\b|"
                         r"\burinary\s+catheter\b|\bindwelling\s+catheter\b"),
    ("gastric_tube", r"\bsonda\s+(?:nasogastrica|naso\s*gastrica|orogastrica)\b|\bsng\b|"
                     r"\bnasogastric\s+tube\b|\bng\s+tube\b"),
    ("npo", r"\bregimen\s+(?:cero|0)\b|\bnada\s+por\s+boca\b|\bayuno\b|\bnpo\b|\bnil\s+by\s+mouth\b"),
    # "Lo dejo en observacion 2 horas" keeps the patient under watch: until
    # 2026-09-24 it was dropped in silence, or held the whole order when a
    # glucose check followed it (rehearsal of the twenty-scenario batch).
    ("monitoring", r"\bmonitor(?:izacion|izar|izado|eo)?\b|\boximetr[ií]a\b|\bpulse\s+ox(?:imetry)?\b|"
                   r"\ben\s+observacion\b|\bunder\s+observation\b|"
                   r"\bcontinuous\s+monitoring\b|\bcardiac\s+monitor\b"),
)


_NAMES_A_DRUG = None


def _support_order(body, verb):
    """A nursing or support order, with the state it is in and no physiology.

    It answers only for a clause that is about the support itself. A clause that
    also names a drug belongs to the ordinary parsing, so a nursing order can
    never speak for — and silently discard — a treatment beside it.
    """
    global _NAMES_A_DRUG
    if _NAMES_A_DRUG is None:
        _NAMES_A_DRUG = re.compile(r"\b(?:" + "|".join(
            pattern for agents in _AGENTS.values() for pattern in agents.values()) + r")\b")
    if _NAMES_A_DRUG.search(body) or re.search(_NAMED_INFUSION, body):
        return None
    named_vital = re.search(r"\b(?:presion|saturacion|frecuencia|spo2|estado mental|perfusion|"
                            r"blood pressure|saturation|heart rate|mental status)\b", body)
    if verb == "monitorizar" and not named_vital:
        return {"type": "monitoring", "operation": "stop" if _operation(verb) == "stop" else "start"}
    for kind, pattern in _SUPPORT_ORDERS:
        if re.search(pattern, body):
            if kind == "monitoring" and re.search(r"\b(?:presion|saturacion|frecuencia|spo2|"
                                                  r"blood pressure|saturation|heart rate)\b", body):
                return None  # "monitoriza la presion" is a reassessment, not a device
            return {"type": kind, "operation": "stop" if _operation(verb) == "stop" else "start"}
    return None


_AIRWAY_CONTEXT = re.compile(r"\b(?:intubacion|intubation|secuencia rapida|rapid sequence|rsi|tubo|"
                             r"vc/ac|pc/ac|ac/vc|psv|ventilacion|ventilator|ventilation|fio2|peep)\b", re.I)


def _names_an_airway_drug(body):
    return any(re.search(r"\b(?:" + pattern + r")\b", body)
               for kind in ("procedural_sedation", "neuromuscular_blockade")
               for pattern in _AGENTS[kind].values())


# Transcutaneous pacing, which is ordered by the pads, the box or the act
# (faculty decision 5, 2026-09-21).
_PACING = (r"\bmarcapaso?s?\s+(?:transcutaneo|externo|transitorio)\b|\bmarcapaso?s?\b(?=[^.]*\b(?:ma|miliamp|por minuto|lpm)\b)"
           r"|transcutaneous pac(?:ing|e|er)|external pac(?:ing|e|er)|\btcp\b|pacing transcutaneo"
           r"|\bpalas de marcapaso|parches de marcapaso")


_PACING_SETTING = re.compile(
    r"^(?:a|at|con|with|de|en)?\s*\d+(?:\.\d+)?\s*"
    r"(?:ma\b|miliamperios?|miliamperes?|milliamps?|milliamperes?|lpm|bpm|"
    r"(?:latidos?\s*)?(?:por|/)\s*min(?:uto)?)", re.I)


# Sending the patient home, and the cardiovascular critical-care bed under every
# name it is given (faculty decisions 1 and 2 of 2026-09-21).
# "La envio a su casa" and "lo mando a domicilio" are how a discharge is
# written; only "a la casa" was listed, so the possessive and the formal word
# both fell through and the disposition produced no action at all. A discharge
# is the trigger of a defined critical event, so the silence removed the event
# with it (2026-09-23).
# "Alta con analgesia oral y control en 7 dias" is a discharge; only the forms
# with "de alta" or a named destination were listed (2026-09-23).
_DISCHARGE = (r"\bde\s+alta\b|\balta\s+(?:a\s+)?(?:domicilio|(?:a\s+)?la\s+casa|medica|hospitalaria)\b"
              r"|^\s*alta\b(?!mente)"
              r"|\bdischarge\b|\bsend(?:\s+\w+)?\s+home\b"
              r"|\ba\s+(?:la\s+|su\s+)?casa\b|\ba\s+domicilio\b")
_CORONARY_UNIT = (r"\buco\b|unidad coronaria|unidad de cuidados coronarios|coronary (?:care )?unit"
                  r"|\bccu\b|(?:cardiac|cardiovascular|coronary)\s+(?:icu|intensive care)|\bcvicu\b"
                  r"|uci coronaria|unidad de cuidados criticos cardiovasculares")
_NAMED_INFUSION = (r"\b(?:nitroglycerin|nitroglicerina|nitro|norepinephrine|noradrenaline|"
                   r"noradrenalina|norepinefrina|norepi|dobutamine|dobutamina)\b")

_VENTILATION_ORDER = re.compile(
    r"\b(?:intubate|intubar|intuba|intubacion|intubación|rsi|rapid sequence|bipap|cpap|niv|vni|"
    r"ventilator|ventilation|ventilacion|ventilación|vmni|vc/ac|pc/ac|ac/vc|psv)\b", re.I)
# The verb that connects a just-intubated patient to the ventilator, with the
# machine named or not. Normalization has already mapped "conecta" to "iniciar".
# It applies only after an airway is placed: "suspende la BiPAP y pon CPAP 8" is
# two deliberate orders, not one.
_AIRWAY_PLACEMENT = re.compile(r"\b(?:intubate|intubar|intubacion|rsi|rapid sequence|secuencia rapida)\b", re.I)
_CONNECTED_SUPPORT = re.compile(
    r"^(?:iniciar|colocar)\s+(?:(?:a|al|en|con)\s+)?"
    r"(?:(?:la|el)\s+)?(?:ventilacion\s+mecanica|ventilador|mechanical\s+ventilation|"
    r"ventilator|ventilation)?\s*", re.I)
_VENTILATION_SETTING = re.compile(
    r"^(?:at\s+|with\s+|a\s+|con\s+|de\s+|en\s+|in\s+|on\s+)?(?:fio2|fio₂|peep|ipap|epap|tidal\s+volume|vt|"
    r"volumen\s+corriente|respiratory\s+rate|set\s+rate|rate|frecuencia|fr\b|flow|flujo|i\s*:\s*e|mode|modo|vc/ac|pc/ac|ac/vc|psv|"
    # "Conectalo a VMNI, BiPAP 14/8": the named mode after a support that has
    # none is that support's setting, not a second, contradictory order.
    r"bipap|cpap|"
    r"pressure\s+support|presion\s+soporte|presión\s+soporte|"
    # The mode written out in either language is a setting of the airway order
    # that precedes it, not a second intubation.
    r"volume\s+control(?:led)?(?:\s+ventilation)?|pressure\s+control(?:led)?(?:\s+ventilation)?|"
    r"assist[- ]control|ventilacion\s+controlada(?:\s+por\s+(?:volumen|presion))?|"
    r"volumen\s+control|presion\s+control|controlada\s+por\s+(?:volumen|presion))\b", re.I)

# The ventilator mode, in both languages and in either word order.
_VC_MODE = (r"\bvc[/ -]?ac\b|volume control(?:led)?|volumen control|control volumen|"
            r"controlada por volumen")
_PC_MODE = (r"\bpc[/ -]?ac\b|pressure control(?:led)?|presion control|control presion|"
            r"controlada por presion")

_COMMAND = re.compile(
    r"^(?:(?:i\s+(?:will|want to)|i'll|i am going to|voy a|quiero|vamos a)\s+)?"
    r"(?P<verb>monitor|assess|vigilar|monitorizar|repeat|repetir|repito|repite|cardiovert|cardiovertir|cardiovierto|give|want|administer|apply|start|initiate|infuse|bolus|order|request|obtain|check|measure|send|get|perform|do|"
    r"stop|discontinue|disconnect|decompress|increase|decrease|lower|raise|titrate|continue|change|set|switch|adjust|modify|reduce|wean|transfuse|nebulize|place|insert|"
    r"consult|call|activate|admit|transfer|discharge|intubate|ventilate|induce|sedate|reassess|re-assess|recheck|reevaluate|"
    r"administrar|administro|administre|aplicar|aplico|colocar|coloco|poner|pongo|dar|doy|dale|d[eé]le|iniciar|inicio|inicie|infundir|indicar|indico|"
    r"solicitar|solicito|solicite|pedir|pido|medir|mido|controlar|control|obtener|realizar|hacer|"
    r"suspender|suspendo|detener|retirar|retiro(?!\s+(?:de|del)\b)|sacar|saco(?!\s+(?:de|del)\b)|"
    r"desconectar|desconecta|desconecto|aumentar|aumento(?!\s+(?:de|del)\b)|disminuir|disminuyo|titular|continuar|mantener|"
    r"ajustar|cambiar|transfundir|transfundo|nebulizar|consultar|interconsultar|llamar|activar|"
    r"hospitalizar|ingresar|trasladar|intubar|intubo|ventilar|reevaluar|reevaluo|revalorar)\b\s*"
)
# Spanish orders are written in the infinitive ("iniciar"), the tu imperative
# ("inicia") or the usted imperative ("inicie"). The verb sets below list one
# form per verb, so a clause-initial imperative is read as its infinitive first.
# The first-person present is how a resident writes the same order ("suspendo la
# dobutamina"). "Activo", "cambio", "bajo" and "aumento" are deliberately absent:
# in clinical Spanish each is an adjective, a noun, a preposition or a noun
# before it is a verb, and each opens sentences that are reasoning.
_ES_IMPERATIVES = {
    "iniciar": "inicia comienza comience empieza empiece comenzar empezar conecta conecte conectar",
    # "pasa un litro" and "cargale 2 g" are how these orders are spoken; each
    # maps to the canonical infinitive the command pattern already knows.
    "administrar": "administra pasa pase pasar paso carga cargue cargar",
    "dar": "da", "poner": "pon ponga",
    # "Instalar" is how a device is ordered at the bedside here. Without it the
    # whole clause had no verb and was dropped in silence, so a transcutaneous
    # pacemaker and a written NIV order vanished from the record (2026-09-21).
    "colocar": "coloca coloque instala instale instalar coloco instalo",
    "aplicar": "aplica aplique aplico", "infundir": "infunde infunda infundo", "indicar": "indica deja deje dejar dejo",
    "pedir": "pide pida", "solicitar": "solicita", "medir": "mide mida",
    "controlar": "controla controle", "obtener": "obten obtenga toma tome tomar obtengo", "realizar": "realiza realice realizo",
    "hacer": "haz haga hago", "suspender": "suspende suspenda suspendo", "detener": "deten detenga detengo",
    "retirar": "retira retire retiro", "sacar": "saca saque saco",
    "aumentar": "aumenta aumente sube suba subir subo", "disminuir": "disminuye disminuya baja baje bajar disminuyo",
    "titular": "titula titule titulo",
    "continuar": "continua continuo", "mantener": "manten mantenga mantengo", "ajustar": "ajusta ajuste ajusto",
    "cambiar": "cambia cambie", "transfundir": "transfunde transfunda transfundo", "nebulizar": "nebuliza nebulice nebulizo",
    "consultar": "consulta consulto", "interconsultar": "interconsulta interconsulte interconsulto",
    "llamar": "llama llame llamo avisa avise avisar aviso", "activar": "activa active",
    "monitorizar": "monitoriza monitorice monitorea monitoree monitorear monitorizo",
    "hospitalizar": "hospitaliza hospitalice hospitalizo", "ingresar": "ingresa ingrese ingreso",
    # Inducing and sedating are the airway drug's own verbs.
    "induce": "induce induzca inducir induzco", "sedate": "seda sede sedar sedo",
    "trasladar": "traslada traslade deriva derive derivar manda mande mandar traslado derivo mando "
                 "envia envie enviar envio", "intubar": "intuba intube", "ventilar": "ventila ventile ventilo",
    "reevaluar": "reevalua reevalue",
}
_ES_IMPERATIVE_FORMS = {form: verb for verb, forms in _ES_IMPERATIVES.items() for form in forms.split()}
# Spanish attaches the pronoun to the imperative: "pasale", "ponle", "subele",
# "ingresalo", "darle". The written accent ("pásale") is already gone by
# normalization, so each form plus its pronoun is the same verb.
_ES_ENCLITICS = ("le", "les", "lo", "la", "los", "las", "selo", "sela")
# Exported: a verb carrying its pronoun is always an order, never a goal, so the
# reasoning capture uses these to know where a priority ends.
_ES_ENCLITIC_FORMS = {
    form + pronoun: verb
    for form, verb in list(_ES_IMPERATIVE_FORMS.items())
    for pronoun in _ES_ENCLITICS
}
_ES_IMPERATIVE_FORMS.update(_ES_ENCLITIC_FORMS)
_ES_IMPERATIVE = re.compile(
    r"(^|[.;\n,+:]\s*|\b(?:y|e(?=\s+h?i)|luego|and|then)\s+)(" + "|".join(sorted(_ES_IMPERATIVE_FORMS, key=len, reverse=True)) + r")\b"
)
# "Empieza a agotarse", "comienza a fatigarse": a verb of beginning followed by
# an infinitive describes the patient. It is an order only when the infinitive
# is one — "empieza a nebulizar salbutamol".
# The infinitive may be reflexive: agotarse, fatigarse, cansarse.
_ES_PERIPHRASIS = re.compile(r"^\s+a\s+(\w+?(?:ar|er|ir))(?:se|me|te|nos)?\b")


# "Deja de pasar el suero" is how stopping is said; "deja indicado" and "deja
# regimen cero" are how an indication is left written. The two need the leading
# phrase resolved before the imperative table sees a bare "deja" (2026-09-21).
_ES_STOP_PERIPHRASIS = re.compile(r"\bdeja(?:r|le|lo|la)?\s+de\s+", re.I)


# First-person forms that are also ordinary nouns. "Aumento del trabajo
# respiratorio" and "retiro del tubo" are descriptions; the same words with a
# direct object are orders (2026-09-21).
_ES_NOUN_FORMS = frozenset({"aumento", "retiro", "saco", "ingreso", "traslado",
                            "mando", "aviso", "titulo", "control", "paso"})
_ES_NOUN_PHRASE = re.compile(r"^\s+(?:de|del)\b")


# Spanish also puts the pronoun *before* the verb, and that is how a resident
# writes the decision that closes an encounter: "lo hospitalizo en sala", "le
# doy aspirina 300 mg vo", "la traslado a UCI". Nothing read the clause-initial
# pronoun, so the clause had no verb: "le doy aspirina" was held as an
# unrecognized order, and "lo hospitalizo" and "le pido un electrocardiograma"
# produced no action and no message at all. Silence is worse than a hold, and it
# fell on the disposition, which is the whole of the continuity domain.
#
# The test is the verb that follows, read from the tables that already exist
# rather than from a third list: a pronoun in front of something the parser
# cannot execute is not an order and is left alone ("la saturacion sigue baja").
_ES_PROCLITIC = re.compile(
    r"(^|[.;\n,+:]\s*|\b(?:y|e(?=\s+h?i)|luego|and|then)\s+)"
    r"(?:(?:me|te|se|nos|le|les|lo|la|los|las)\s+){1,2}(\w+)\b"
)


# "Given the hypoxemia I will start NIV" and "como esta hipotenso le voy a pasar
# volumen" announce an order in the middle of a sentence that opens with the
# reason for it. The command pattern is anchored to the start of a clause, so
# without a comma the order was read as prose and nothing happened at all —
# neither an execution nor a question (measured 2026-09-23). A declared
# intention starts its own clause.
_DECLARED_INTENTION = re.compile(
    r"(?<=[^.;,\n])\s+(?=(?:i\s+(?:will|am\s+going\s+to)|i'll|i'm\s+going\s+to|"
    r"(?:le\s+|les\s+)?voy\s+a|vamos\s+a)\s+\w)", re.I)


# In Spanish the intention is a periphrasis around the infinitive the parser
# already knows: "le voy a pasar volumen" is "pasar volumen" announced. Removing
# the periphrasis puts the infinitive where a clause-initial order belongs.
_ES_INTENTION = re.compile(
    r"(^|[.;,\n]\s*)(?:(?:me|te|se|nos|le|les|lo|la|los|las)\s+)?"
    r"(?:voy\s+a|vamos\s+a)\s+(?=\w)", re.I)


def _declared_intention(text):
    return _ES_INTENTION.sub(r"\1", _DECLARED_INTENTION.sub(", ", str(text or "")))


def _spanish_proclitics(text):
    """Drop a pronoun standing between the clause and its verb."""
    def replace(match):
        form = match[2]
        if form in _ES_IMPERATIVE_FORMS:
            # Resolved here rather than by the pass below, because the pronoun
            # already settles what these words are: "el ingreso del paciente" is
            # a noun, "lo ingreso" is not, and the noun guard there would put
            # the order back to sleep.
            return match[1] + _ES_IMPERATIVE_FORMS[form]
        return match[1] + form if _COMMAND.match(match.string[match.start(2):]) else match[0]
    return _ES_PROCLITIC.sub(replace, text)


# "Parto con volumen", "partamos con noradrenalina": a periphrasis of beginning.
# "Parto" on its own is a noun in clinical Spanish, so only the form that takes
# "con" is read as the order it is.
_ES_START_PERIPHRASIS = re.compile(
    r"\b(?:partir|parto|parte|partamos|partimos|arrancar|arranco|"
    r"comenzar|comienzo)\s+con\s+", re.I)


def _spanish_imperatives(text):
    """Read a clause-initial imperative as the infinitive the parser knows."""
    text = _ES_STOP_PERIPHRASIS.sub("suspender ", text)
    text = _ES_START_PERIPHRASIS.sub("administrar ", text)
    def replace(match):
        if match[2] in _ES_NOUN_FORMS and _ES_NOUN_PHRASE.match(match.string[match.end():]):
            return match[0]
        following = _ES_PERIPHRASIS.match(match.string[match.end():])
        if following and following[1] not in _ES_IMPERATIVE_FORMS.values():
            return match[0]
        return match[1] + _ES_IMPERATIVE_FORMS[match[2]]
    return _ES_IMPERATIVE.sub(replace, text)


# Orders the engine recognises and does not execute: medicines with no modelled
# effect here, and what is prescribed for after discharge. A resident who wrote
# one had the whole submission held until they replaced it (rehearsal of the
# twenty-scenario batch, 2026-09-24). Whether any of them should act on the
# physiology is a clinical decision (docs/DECISIONES_CLINICAS_PENDIENTES.md).
_UNMODELED_ORDER = re.compile(
    r"\b(?:clorfenamina|clorfeniramina|chlorphenamine|chlorpheniramine|difenhidramina|diphenhydramine|"
    r"antihistaminic[oa]s?|antihistamines?|cetirizina|cetirizine|loratadina|loratadine|desloratadina|"
    r"hidroxicina|hydroxyzine|famotidina|famotidine|ranitidina|ranitidine|"
    r"lorazepam|diazepam|alprazolam|clonazepam|benzodiacepinas?|benzodiazepines?|"
    r"ondansetron|metoclopramida|metoclopramide|"
    r"autoinyector|autoinjector|epi-?pen)\b"
    r"|\b(?:indic\w*|recet\w*|prescrib\w*)\b.*\b(?:al|para\s+el)\s+alta\b"
    r"|\b(?:prescribe|prescribed)\b.*\b(?:at|on|for)\s+discharge\b")

# What a patient takes, named by drug or by class, after "toma" or "usa".
_TAKES_MEDICATION = re.compile(
    r"\b(?:glibenclamida|glipizida|gliclazida|glimepirida|sulfonilureas?|metformina|insulinas?|"
    r"hipoglicemiantes?|betabloqueador(?:es)?|beta\s*bloqueador(?:es)?|propranolol|atenolol|"
    r"metoprolol|bisoprolol|carvedilol|bloqueador(?:es)?\s+de(?:l)?\s+calcio|calcioantagonistas?|"
    r"verapamilo|diltiazem|amlodipino|nifedipino|anticoagulantes?|acenocumarol|warfarina|"
    r"rivaroxaban|apixaban|dabigatran|antiagregantes?|aspirina|clopidogrel|opioides?|tramadol|"
    r"morfina|metadona|oxicodona|fentanilo|benzodiacepinas?|clonazepam|alprazolam|diazepam|"
    r"antihipertensivos?|enalapril|losartan|diureticos?|furosemida|digoxina|litio|"
    r"(?:sus|mis|los|unos|algunos)\s+(?:remedios|medicamentos|pastillas|farmacos)|"
    r"remedios|medicamentos|pastillas)\b")

_DIAG_VERBS = {
    "want", "order", "request", "obtain", "check", "measure", "send", "get", "perform", "do",
    "solicitar", "solicito", "solicite", "pedir", "pido", "medir", "mido", "controlar",
    "control", "obtener", "realizar", "hacer", "recheck",
}
_NON_ORDER = re.compile(
    r"\b(?:i think|i suspect|i believe|i expect|i anticipate|i hope|my hypothesis|my impression|"
    r"my working model|my working diagnosis|my priority|my plan|working diagnosis|because|need to improve|to improve|should improve|would improve|may improve|"
    r"pienso|creo|sospecho|espero|anticip[oae]|mi hipotesis|mi impresion|mi plan|porque|para mejorar|"
    r"(?:mi|la|el|nuestra|nuestro)\s+(?:prioridad|objetivo|meta))\b"
)
# How a discharge instruction is written, in both languages. The condition that
# follows one of these belongs to the advice, not to the order before it.
_ADVICE_CLAUSE = re.compile(
    r"\b(?:con\s+(?:indicaci[oó]n(?:es)?|instrucci[oó]n(?:es)?)\s+de|"
    r"con\s+control(?:\s+\w+)?\s+(?:en|a\s+las)|"
    r"indic[aáo]ndole\s+|indic(?:ar|o|ando)(?:le)?\s+(?=\w)|"
    r"with\s+instructions\s+to|advised\s+to|told\s+to|"
    r"safety[- ]net(?:ting)?|return\s+precautions?)\b", re.I)
_CONDITIONAL = re.compile(
    r"\b(?:if|unless|consider|considering|might|could|would|perhaps|maybe|si|salvo que|considerar|considero|podria|quizas|tal vez)\b"
)
_NEGATION = re.compile(r"^(?:please\s+)?(?:do not|don't|dont|never|avoid|no|not|sin|evitar|evito)\b")
_OXYGEN_DEVICES = (
    ("nasal cannula", r"nasal cann?ula|canula nasal|naricera|nasal prongs|nc"),
    # A reservoir mask is named after its bag or after its recirculation; both
    # are the same device (2026-09-21), and it used to execute as a simple mask.
    ("non-rebreather mask", r"non[- ]rebreather(?: mask)?|non[- ]rebreathing mask|nrb|"
                            r"mascarilla(?:\s+(?:con|de))?\s+reservorio|mascara(?:\s+(?:con|de))?\s+reservorio|"
                            r"mascarilla\s+(?:de|con)\s+recirculacion|mascara\s+(?:de|con)\s+recirculacion|"
                            # Its commonest Spanish name says what it does not do:
                            # "de no recirculacion", "no recirculante", "de no
                            # reinhalacion". Read as a simple mask until 2026-09-24.
                            r"(?:mascarilla|mascara)\s+(?:de\s+)?no\s+(?:recirculacion|recirculante|reinhalacion)|"
                            r"\bno\s+(?:recirculante|reinhalacion)\b"),
    # A bare "mask" or "mascarilla" is the simple face mask: it is how oxygen is
    # ordered at the bedside, in both languages. The specific devices above also
    # contain the word, so ``devices`` keeps the longer match and drops this one.
    ("simple mask", r"simple (?:face )?mask|mascarilla simple|mascara simple|face mask|mask|mascarilla|mascara"),
    ("room air", r"room air|aire ambiente"),
)
_OXYGEN_DEVICE_EXAMPLES = "nasal cannula 4 L/min, simple mask 8 L/min or non-rebreather mask 15 L/min"
_OXYGEN_MENTION = r"\b(?:oxygen|oxigeno|o2|nasal cann?ula|canula nasal|naricera|nasal prongs|nc|non[- ]rebreather|non[- ]rebreathing|nrb|simple mask|mascarilla|mascara|room air|aire ambiente)\b"
# "Cuatro litros por minuto" is how the flow is spoken and written; the
# abbreviations were already read (2026-09-21).
_FLOW = r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(?:l\s*/\s*(?:min|m)\b|lpm|lts?\s*/\s*min|(?:lts?|l)(?![\w/]|\s*/)|liters?\s*/\s*min|litres?\s*/\s*min|litros?\s*/\s*min|(?:liters?|litres?|litros?)(?:\s+(?:por|per)\s+(?:minuto|min|minute))?)\b"




# Examining the patient, written as an order rather than clicked in the Examine
# control: "examina el abdomen", "ausculta el torax", "revisa el neurologico".
# First person as well as the imperative: faculty write "examino las piernas",
# not "examina las piernas", and the examination was simply lost (2026-09-22).
_EXAMINATION_VERBS = (r"examinar|examina|examino|examine|examine[ns]|explorar|explora|exploro|"
                      r"auscultar|ausculta|ausculto|auscultate|palpar|palpa|palpo|palpate|"
                      r"revisar|revisa|reviso|inspeccionar|inspecciona|inspecciono|inspect|"
                      r"busco|buscar|busca")
_EXAMINATION_REGIONS = (
    ("General appearance", r"apariencia\s+general|aspecto\s+general|estado\s+general|general\s+appearance|"
                           r"aspecto\s+del?\s+paciente"),
    ("Breathing", r"respiraci[oó]n|patr[oó]n\s+respiratorio|breathing|trabajo\s+respiratorio|"
                  r"work\s+of\s+breathing"),
    ("Peripheral perfusion", r"perfusi[oó]n(?:\s+perif[eé]rica)?|llene\s+capilar|peripheral\s+perfusion|"
                             r"capillary\s+refill"),
    # The legs are their own examination, not a reading of perfusion. "Examine
    # the extremities" was refused and "examina las extremidades" answered with
    # the capillary refill, so the calf swelling that turns "maybe it is
    # anxiety" into a pulmonary embolism could not be asked for in either
    # language (played 2026-09-22). Where a case authors no finding there, the
    # engine still answers with the perfusion it always had.
    ("Extremities", r"extremidades|extremities|extremidad|extremity|piernas|legs|pierna|leg|"
                    r"pantorrillas?|calf|calves|miembros\s+inferiores|gemelos"),
    ("Cardiac", r"cardiaco|card[ií]aco|coraz[oó]n|cardiac|heart|cardiovascular"),
    ("Respiratory", r"respiratorio|pulmones|pulmonar|t[oó]rax|chest|lungs|respiratory|campos\s+pulmonares"),
    ("Abdomen", r"abdomen|abdominal|vientre"),
    ("Neurological", r"neurol[oó]gico|neurol[oó]gica|neurologic(?:al)?|neuro\b|estado\s+neurol[oó]gico|"
                     r"examen\s+neurol[oó]gico"),
)


def _examination_order(body, verb=None):
    """The region a written examination asks for, or None.

    A clause may carry the verb ("examino el abdomen") or inherit it from the
    one before it ("examino la respiracion, el abdomen y el corazon"). Until
    2026-09-23 only the first clause was an examination and the rest were quoted
    back as unreadable orders, so examining a patient properly held the turn.
    """
    inherited = str(verb or "") in _EXAMINATION_VERBS.split("|")
    if not inherited and not re.search(r"\b(?:" + _EXAMINATION_VERBS + r")\b", body):
        return None
    for region, pattern in _EXAMINATION_REGIONS:
        if re.search(r"\b(?:" + pattern + r")\b", body):
            return region
    return ""


def _clarification(message):
    return {"type": "clarification", "message": message}


# An explicit instruction to wait for a result before acting. Deliberately
# narrow: it has to name the waiting, not merely sequence two orders, because
# "give oxygen and then reassess" is not a dependency and must keep parsing as
# it always has.
_WAIT_FOR_RESULT = re.compile(
    r"\s*(?:,\s*)?(?:y\s+|and\s+)?"
    r"(?:(?:espero|espera|esperar|esperamos|esperemos|aguardo|aguarda|aguardar)\s+"
    r"(?:(?:el|los|la|las)\s+)?(?:resultados?\b|\w+)"
    r"|(?:una\s+vez\s+que\s+)?(?:cuando|una\s+vez)\s+(?:llegue|llegen|lleguen|vuelva|vuelvan|"
    r"est[eé]|est[eé]n|tenga|tengamos|salga|salgan)"
    r"|(?:tras|con|despu[eé]s\s+de|segun|seg[uú]n)\s+(?:el|los|la|las)\s+resultados?"
    r"|wait\s+for\s+(?:the\s+)?(?:results?\b|\w+)"
    r"|once\s+(?:the\s+)?\w+\s+(?:is|are)\s+back"
    r"|(?:after|with)\s+the\s+results?"
    r"|when\s+(?:the\s+)?\w+\s+(?:comes?|returns?)\s+back)"
    r"[^.;]*?(?:,\s*|\s+)(?:y\s+|and\s+)?"
    r"(?:luego|despu[eé]s|entonces|then|after\s+that|posteriormente)\s+",
    re.I)


def _sequenced(normalized):
    """Split an entry that says to wait for a result before acting.

    Returns ``(what_waits, what_happens_now)``. The text is left untouched when
    nothing says to wait, so every entry that is not a dependency parses exactly
    as it did before.
    """
    match = _WAIT_FOR_RESULT.search(normalized)
    if not match:
        return "", normalized
    return normalized[match.end():].strip(), normalized[:match.start()].strip(" ,")


#: A procedure only one service performs. Naming it is asking for that service.
_SERVICE_PROCEDURE = (r"nefrostom[ií]a|nephrostomy|cat[eé]ter\s+doble\s+j|doble\s+j|"
                      r"double[- ]j|ureteral\s+stent|stent\s+ureteral")


# The physiologic direction a resident states as a goal or an expectation.
_GOAL_VERB = (r"sub[ai]r|bajar|mejorar|aumentar|disminuir|reducir|limitar|controlar|"
              r"corregir|estabilizar|aliviar|revertir|frenar|mantener|prevenir|evitar|"
              r"lograr|conseguir|optimizar|descargar|oxigenar|perfundir|compensar|"
              r"raise|lower|improve|increase|decrease|reduce|limit|control|correct|"
              r"stabili[sz]e|relieve|reverse|maintain|prevent|avoid|achieve|"
              r"optimi[sz]e|unload|restore|support")

# What a resident watches. These are read off a monitor or a chart; none of them
# is a region of the physical examination.
_MONITORED_VARIABLE = (r"presi[oó]n(?:\s+arterial)?|pam|pas|pad|ta\b|frecuencia(?:\s+\w+)?|fc\b|fr\b|"
                       r"saturaci[oó]n|spo2|sat\b|hgt|glicemia|glucemia|glucosa|diuresis|"
                       r"d[eé]bito\s+urinario|gasto\s+urinario|llene\s+capilar|perfusi[oó]n|"
                       r"conciencia|estado\s+mental|ritmo|lactato|temperatura|dolor|ecg|"
                       r"bp\b|hr\b|rr\b|map\b|saturation|mental\s+status|perfusion|rhythm|"
                       r"capillary\s+refill|urine\s+output|lactate|pain|glucose")

# A clause that states why, what for, or what will be watched is reasoning, and
# reasoning is not an unreadable order.
#
# Found on 2026-09-23 measuring fifteen orders that named all four categories in
# ordinary prose: eight of them had a reasoning clause quoted back as "This order
# was not recognized" — "quiero frenar la agregacion", "the goal is to limit
# thrombus growth", "apunto a PAM sobre 65", "controlo PAM", "llene capilar".
# The resident had written exactly what the simulator asks for and the simulator
# held the turn over it. These clauses produce nothing here; the reasoning
# extractor reads them into the slots they belong to.
_REASONING_CLAUSE = re.compile(
    r"^\s*(?:[,;]\s*)?(?:y|e|and|then|luego)?\s*(?:"
    r"(?:quiero|busco|buscando|apunto|apuntando|pretendo|intento|espero|anticipo|preveo|"
    r"me\s+interesa|la\s+idea\s+es|mi\s+(?:objetivo|meta|prioridad)|el\s+(?:objetivo|fin)|"
    r"la\s+(?:prioridad|meta)|i\s+want|i\s+aim|i\s+expect|i\s+anticipate|i\s+hope|"
    r"my\s+(?:goal|aim|priority)|the\s+(?:goal|aim|idea|priority|plan)|hoping|looking\s+to)\b"
    r"|(?:para|to|a\s+fin\s+de|con\s+el\s+fin\s+de|in\s+order\s+to)\s+(?:" + _GOAL_VERB + r")\b"
    r")", re.I)

_WATCHED_CLAUSE = re.compile(
    r"^\s*(?:[,;]\s*)?(?:y|e|and|then|luego)?\s*"
    r"(?:(?:" + _EXAMINATION_VERBS + r"|controlo|controlar|controla|chequeo|chequear|"
    r"vigilo|vigilar|mido|medir|monitorizo|monitorizar|monitoreo|monitorear|"
    r"control(?:es)?|check|monitor|watch|follow|recheck|track)\s+)?"
    # The clause reaches here with its verb already removed, so "control de PAM"
    # arrives as "de pam": the particles between the verb and the variable are
    # optional and repeatable.
    r"(?:(?:de|del|el|la|los|las|the|of|a|al)\s+)*(?:" + _MONITORED_VARIABLE + r")\b",
    re.I)

# The disturbance a resident says they are trying to move. This list is closed
# on purpose: a bare infinitive with an open-ended object reads "reducir la
# dobutamina" as a goal and drops a titration order in silence, which is worse
# than any spurious question this guard was written to remove.
_PHYSIOLOGIC_TARGET = (r"congesti[oó]n|precarga|poscarga|postcarga|disnea|hipoxemia|hipoxia|"
                       r"hipotensi[oó]n|hipertensi[oó]n|taquicardia|bradicardia|acidosis|"
                       r"agregaci[oó]n|broncoespasmo|inflamaci[oó]n|isquemia|edema|sangrado|"
                       r"hemorragia|fiebre|agitaci[oó]n|ansiedad|s[ií]ntomas|trabajo\s+respiratorio|"
                       r"esfuerzo\s+respiratorio|obstrucci[oó]n|shock|sepsis|infecci[oó]n|"
                       r"congestion|preload|afterload|dyspnea|dyspnoea|hypoxemia|hypoxaemia|"
                       r"hypotension|hypertension|tachycardia|bradycardia|acidosis|aggregation|"
                       r"bronchospasm|inflammation|ischemia|ischaemia|edema|oedema|bleeding|"
                       r"haemorrhage|hemorrhage|fever|agitation|anxiety|symptoms|"
                       r"work\s+of\s+breathing|obstruction|thrombus|clot|infection")

# A bare infinitive can be a goal ("disminuir la congestion") or an order
# ("bajar la nitroglicerina a 20"). What separates them is what is being moved:
# a disturbance, or a drug.
_GOAL_INFINITIVE = re.compile(
    r"^\s*(?:[,;]\s*)?(?:y|e|and|then|luego)?\s*(?:(?:" + _GOAL_VERB + r")\s+)"
    r"(?:(?:el|la|los|las|the|su)\s+)?(?:" + _PHYSIOLOGIC_TARGET + r"|"
    + _MONITORED_VARIABLE + r")\b", re.I)


def _is_reasoning(body):
    """True when a clause states a goal, an expectation, or what will be watched.

    The guard is deliberately one-sided: a clause naming an administered
    quantity is an order whatever else it says, so "adrenalina 0.5 mg IM" is
    still quoted back as unsupported rather than quietly read as a wish.
    """
    text = " ".join(str(body or "").split())
    if not text or _ADMINISTERED_QUANTITY.search(text):
        return False
    return bool(_REASONING_CLAUSE.match(text) or _WATCHED_CLAUSE.match(text)
                or _GOAL_INFINITIVE.match(text))


# A quantity that can only be administered: volume, dose, or shock energy. The
# units of description — mmHg, %, mmol/L, bpm, minutes — are deliberately absent.
_ADMINISTERED_QUANTITY = re.compile(
    r"\d(?:[.,]\d+)?\s*(?:ml|cc|mcg|ug|mg|gr?|units?|unidades?|ui|iu|joules?|j\b|"
    r"l(?:t|ts|iters?|itres?|itros?)?\b)", re.I)
# What is left of a clause once its numbers, units, routes and particles are
# removed: a bare "500 mL" is an answer to a question, not an order.
_QUANTITY_ONLY = re.compile(
    r"\b(?:ml|cc|mcg|ug|mg|gr?|units?|unidades?|ui|iu|joules?|j|l|lt|lts|liters?|litres?|litros?|"
    r"iv|io|po|im|sc|sl|min|mins?|minutos?|minutes?|hora?s?|hours?|de|del|la|el|los|las|un|una|"
    r"por|para|a|al|en|the|of|over|durante|y|and)\b|[\d.,%/]+", re.I)


# A clause whose numbers report what already happened, or say what must not
# happen, is not an order the resident is waiting to see executed.
_REPORTS_OR_WITHHOLDS = re.compile(
    r"\b(?:received|receives|was given|were given|already|previously|had|has|have|"
    r"after|following|improved|worsened|responded|no|not|never|without|"
    r"recibio|recibe|ya|previamente|tras|despues|luego de|mejoro|empeoro|respondio|sin|"
    # Urine is the one volume the patient produces rather than receives, so a
    # millilitre attached to it is a measurement. Found playing the left main
    # case (2026-09-22): "diuresis de 54 mL/h" inside the finding was quoted back
    # as an unrecognized order and held the whole submission.
    r"diuresis|gasto urinario|debito urinario|urine output|urinary output)\b", re.I)


def _names_a_substance(body):
    """True when the clause says more than a quantity: something was ordered."""
    return len(_QUANTITY_ONLY.sub(" ", body).strip()) >= 3


def _unreadable(piece):
    """Quote an order back: a resident cannot repair an item that was never named."""
    fragment = " ".join(str(piece).split())[:80]
    return {**_clarification(
        f'This order was not recognized: "{fragment}". Replace it with a supported '
        "intervention, dose/settings and route, or say cancel. The other orders in "
        "this submission are held until then."), "unrecognized_text": fragment}






# Airway drugs are written by weight and run as infusions; the other classes are
# not (faculty decision 11, 2026-09-21).
_WEIGHT_BASED = frozenset({"procedural_sedation", "neuromuscular_blockade", "opioid_analgesia"})
_INFUSION_RATE = re.compile(r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(mg|mcg|ug)\s*/\s*(?:(kg)\s*/\s*)?(min|h|hr|hora|hour)\b", re.I)
_PER_KILO = re.compile(r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(mg|mcg|ug)\s*/\s*kg(?!\s*/)", re.I)


def _medication(text, kind, agent):
    dose, units = _amount(text, r"mcg|ug|mg|grams?|gramos?|g|units?|unidades|ui|u")
    if kind in _WEIGHT_BASED:
        infusion = _INFUSION_RATE.search(text)
        if infusion:
            rate = float(infusion[1]) / (1000 if infusion[2].lower() in {"mcg", "ug"} else 1)
            per_unit = ("mg/kg/" if infusion[3] else "mg/") + ("h" if infusion[4].lower().startswith(("h", "hora")) else "min")
            return {"type": "sedation_infusion", "agent": agent, "rate": rate,
                    "units": per_unit, "route": _route(text) or "IV", "operation": "start"}
        per_kilo = _PER_KILO.search(text)
        if per_kilo:
            value = float(per_kilo[1]) / (1000 if per_kilo[2].lower() in {"mcg", "ug"} else 1)
            return {"type": kind, "agent": agent, "dose_mg_per_kg": value, "route": _route(text)}
    # A weight/rate-based order cannot be flattened into a single fixed dose.
    if re.search(r"(?:mg|mcg|ug|g|units?|ui|u)\s*/\s*(?:kg|min|h|hr|hour)", text):
        return _clarification("Specify a supported fixed dose and route; this medication order uses weight or infusion-rate units.")
    route = _route(text)
    if kind == "anticoagulation":
        unit_name = "units" if units in {"unit", "units", "unidades", "ui", "u"} else units
        if units in {"g", "gram", "grams", "gramo", "gramos"}:
            dose, unit_name = dose * 1000, "mg"
        return {"type": kind, "agent": agent, "dose": dose, "units": unit_name, "route": route}
    if units in {"unit", "units", "unidades", "ui", "u"}:
        return _clarification("Specify the medication dose in mass units (mg or g), not units.")
    mg = dose
    if dose is not None and units in {"g", "gram", "grams", "gramo", "gramos"}:
        mg = dose * 1000
    elif dose is not None and units in {"mcg", "ug"}:
        mg = dose / 1000
    if kind == "dextrose":
        return {"type": kind, "dose_g": mg / 1000 if mg is not None else None, "route": route}
    return {"type": kind, "agent": agent, "dose_mg": mg, "route": route}


def _operation(verb):
    if verb in {"stop", "discontinue", "suspender", "suspendo", "detener", "retirar", "retiro", "sacar", "saco"}:
        return "stop"
    if verb in {"increase", "decrease", "lower", "raise", "titrate", "change", "set", "switch", "adjust", "modify", "reduce", "wean", "aumentar", "aumento", "disminuir", "disminuyo", "titular", "ajustar", "cambiar"}:
        return "adjust"
    if verb in {"continue", "continuar", "mantener"}:
        return "continue"
    return "start"


def _settings(text, name):
    if name == "fio2" and not re.search(r"\bfio2\b", text):
        # O2 expressed as a percentage is a respiratory setting, not a flow.
        text = re.sub(r"\bo2(?=\s*(?:of|de|=|at|to|a)?\s*[-.\d]+\s*%)", "fio2", text)
    # "FiO2 del ventilador a 80%": the setting may name the machine it belongs to,
    # and Spanish contracts "a el" into "al". Nothing else may come between the
    # name and its value, so "FiO2 and PEEP 5" never reads 5 as the FiO2.
    match = re.search(r"\b" + name + r"\s*(?:del?\s+(?:la\s+)?ventilador|of\s+the\s+ventilator)?"
                      r"\s*(?:of|de|=|at|to|al|a)?\s*(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(%)?", text)
    if not match:
        return None
    value = float(match[1])
    # FiO2 can be explicitly written as a fraction or percentage.
    return value * 100 if name == "fio2" and 0 < value <= 1 and not match[2] else value


def _ventilator_extras(body):
    """Tidal volume, set rate, inspiratory flow and I:E written in any usual form."""
    extras = {}
    per_kg = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|cc)\s*/\s*kg", body)
    fixed = re.search(r"\b(?:vt|tidal\s+volume|volumen\s+corriente)\s*(?:of|de|=|at|to|a)?\s*"
                      r"(\d+(?:\.\d+)?)\s*(?:ml|cc)?\b", body)
    if per_kg:
        extras["tidal_ml_per_kg"] = float(per_kg[1])
    elif fixed:
        extras["tidal_volume_ml"] = float(fixed[1])
    rate = re.search(r"\b(?:rr|respiratory\s+rate|set\s+rate|rate|"
                     r"frecuencia(?:\s+(?:respiratoria|del\s+ventilador))?|fr)\s*"
                     r"(?:del?\s+ventilador)?\s*(?:of|de|=|at|to|al|a)?\s*(\d+(?:\.\d+)?)\s*(?:/\s*min|per\s+min(?:ute)?|bpm|por\s+minuto)?\b", body)
    if rate:
        extras["rate_per_min"] = float(rate[1])
    flow = re.search(r"\b(?:flow|flujo)\s*(?:of|de|=|at|to|a)?\s*(\d+(?:\.\d+)?)\s*(?:l\s*/\s*min|lpm|l\s+por\s+minuto)\b", body)
    if flow:
        extras["flow_l_per_min"] = float(flow[1])
    ratio = re.search(r"\b(?:i\s*:\s*e|ie|relaci[oó]n\s*i\s*:?\s*e)\s*(?:of|de|=|at|to|a)?\s*1\s*:\s*(\d+(?:\.\d+)?)", body)
    if ratio:
        extras["ie_expiratory_ratio"] = float(ratio[1])
    return extras


def _oxygen_order(body, verb):
    """Bind the device and flow to the explicit target, never the prior setting."""
    if _operation(verb) == "stop":
        return {"type": "oxygen", "device": "room air", "flow_lpm": 0}
    if re.search(r"\b(?:high[- ]flow|hfnc|alto flujo)\b", body):
        return _clarification("High-flow oxygen is not a supported device in this encounter. Specify an available oxygen device and flow (for example, " + _OXYGEN_DEVICE_EXAMPLES + ").")
    if _operation(verb) == "adjust" and re.search(r"\b(?:by|en)\s+-?\d", body):
        return _clarification("Specify the absolute target oxygen flow in L/min, not a relative change.")

    def devices(segment):
        matches = [(match.start(), match.end(), name) for name, pattern in _OXYGEN_DEVICES
                   for match in re.finditer(r"\b(?:" + pattern + r")\b", segment)]
        # "non-rebreather mask" contains a bare "mask", and "mascarilla con
        # reservorio" a bare "mascarilla": the named device wins over the span
        # it encloses, so one order never reads as two devices.
        kept = [m for i, m in enumerate(matches)
                if not any(other[0] <= m[0] and m[1] <= other[1] and other[1] - other[0] > m[1] - m[0]
                           for j, other in enumerate(matches) if j != i)]
        return [name for _, _, name in sorted(kept)]

    target = body
    transition = re.search(r"\b(?:from|desde|de)\b.+?\b(?:to|a)\b\s*(.+)$", body)
    if transition:
        target = transition[1]
    selected = set(devices(target))
    if not selected and transition and verb not in {"switch", "cambiar"}:
        # "Increase nasal cannula from 3 to 4 L/min" retains its explicitly
        # named device. A request to switch interfaces must name the new one.
        selected = set(devices(body[:transition.start(1)]))
    if len(selected) > 1 or (not selected and (verb in {"switch", "cambiar"} or _operation(verb) not in {"adjust", "continue"})):
        return {**_clarification("Specify one target oxygen device and its flow in L/min (for example, " + _OXYGEN_DEVICE_EXAMPLES + ")."),
                **({"pending_action": {"type": "oxygen", "device": None, "flow_lpm": float(re.search(_FLOW, target)[1]) if re.search(_FLOW, target) else None}} if not selected and verb not in {"switch", "cambiar"} and len(list(re.finditer(_FLOW, target))) <= 1 else {})}
    device = selected.pop() if selected else None
    if device == "room air":
        return {"type": "oxygen", "device": device, "flow_lpm": 0}
    flows = list(re.finditer(_FLOW, target))
    if len(flows) > 1 or (not flows and _operation(verb) not in {"adjust", "continue"}):
        return {**_clarification("Specify one absolute target oxygen flow in L/min (for example, " + _OXYGEN_DEVICE_EXAMPLES + ")."),
                **({"pending_action": {"type": "oxygen", "device": device, "flow_lpm": None}} if not flows else {})}
    return {"type": "oxygen", "device": device, "flow_lpm": float(flows[0][1]) if flows else None, **({"operation": _operation(verb)} if _operation(verb) in {"adjust", "continue"} and (device is None or not flows) else {})}


_DISPOSITION_VERBS = frozenset({"admit", "transfer", "discharge", "dar de alta",
                                "hospitalizar", "ingresar", "trasladar"})


def _parse_piece_core(piece, inherited=None):
    if re.fullmatch(r"\s*(?:prepare|set up|get ready|preparar|prepara)(?:\s+(?:for|para))?\s+(?:intubation|intubacion|airway|via aerea)\s*[.!]?", piece):
        return [{"type": "airway_preparation"}], "prepare"
    text = piece.strip(" :")
    text = re.sub(r"^(?:please|por favor|then|luego|despues)\s+", "", text)
    command = _COMMAND.match(text)
    verb = command["verb"] if command else inherited
    # A disposition names one destination and takes no list. "Hospitalizar en
    # sala para continuar broncodilatadores y corticoides" is one admission and
    # a purpose; inherited, the trailing "corticoides" became a second
    # admission with nowhere to go, and its clarification held the whole
    # submission, so the disposition that was written never executed. Found by
    # playing the asthma case for the rubric pilot (2026-09-23).
    if command is None and verb in _DISPOSITION_VERBS:
        return [], None
    body = text[command.end():].strip() if command else text
    if _NEGATION.match(body):
        return [], None
    # Reasoning following a valid order belongs to reasoning extraction, not to
    # this parser. A medication mentioned there cannot become a second order.
    boundary = _NON_ORDER.search(body)
    if boundary:
        body = body[:boundary.start()].strip(" ,:")
    # Observing saturation is not administering oxygen. Keep this distinction
    # before diagnostic and treatment matching, including inherited list verbs.
    observational = verb in {"monitor", "assess", "vigilar", "monitorizar", "check", "recheck", "measure", "medir", "mido", "controlar", "control"} or bool(re.match(r"(?:monitor(?:ing)?|monitorizar|vigilar)\b", body))
    vital = re.search(r"\b(?:blood pressure|bp|heart rate|hr|respiratory rate|rr|oxygen saturation|o2 saturation|spo2|saturation|sats|oxygen levels|presion arterial|saturacion|frecuencia cardiaca|frecuencia respiratoria|perfusion|breathing|respiratory effort|oxigeno|rhythm|mental status|capillary refill|crt|estado mental)\b", body)
    if observational and vital:
        delay, _ = _amount(body, r"minutes?|mins?|minutos?")
        if re.search(r"\b(?:hours?|horas?|seconds?|segundos?)\b", body):
            return [_clarification("Specify the reassessment interval in minutes.")], verb
        return [{"type": "reassessment", "delay_min": delay if delay is not None else 0}], verb if verb in _DIAG_VERBS else "monitor"
    if re.search(r"\b(?:saturation|saturacion|spo2|sats|oxygen levels)\b", body) and not re.search(_FLOW, body) and verb in {"increase", "decrease", "set", "aumentar", "disminuir", "ajustar"}:
        return [_clarification("An oxygen saturation target is not a device or flow order. Specify the oxygen device and flow to administer.")], verb
    # A bare "hospitalizalo" or "dale de alta" is a real disposition order with a
    # question attached, not nothing at all (2026-09-21).
    if not body and verb not in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar",
                                 "intubate", "intubar", "intubo",
                                 "admit", "transfer", "discharge", "hospitalizar", "ingresar", "trasladar"}:
        return [], verb

    if verb in {"repeat", "repetir", "repito", "repite"} or re.match(r"(?:another|more|otro|otra|otros|otras)\b", body):
        studies = [name for name, pattern in _DIAGNOSTICS.items() if re.search(r"\b(?:" + pattern + r")\b", body)]
        if studies:
            return [{"type": "diagnostic", "diagnostic": name} for name in studies], verb
        quantity_text = re.split(r"\b(?:over|durante|en)\s+[-.\d]", body)[0]
        if len(re.findall(r"(?<![\w.])-?(?:\d+(?:\.\d+)?|\.\d+)\s*(?:ml|cc|l|lt|mg|g|mcg|ug)\b", quantity_text)) > 1:
            return [_clarification("Specify one quantity for the treatment to repeat.")], verb
        target = "fluid" if re.search(r"\b(?:bolus|fluid|saline|ns|sf|ringer|ringers|lr|crystalloid|cristaloides?|bolo|suero|ml|cc)\b", body) else None
        agent = next((name for agents in _AGENTS.values() for name, pattern in agents.items() if re.search(r"\b(?:" + pattern + r")\b", body)), None)
        value, unit = _amount(body, r"ml|cc|l|lt|mg|g|mcg|ug")
        if value is None and re.search(r"\d", quantity_text):
            return [_clarification("Specify explicit units for the quantity to repeat.")], verb
        if target is None and agent is None and not re.fullmatch(r"(?:the )?(?:same|previous)(?: (?:treatment|dose|medication))?|(?:el |la )?(?:mismo|misma|anterior)(?: (?:tratamiento|dosis|medicamento))?", body):
            return [_clarification("Specify which recorded drug or fluid to repeat.")], verb
        fluid_type = None
        if target == "fluid":
            if re.search(r"\b(?:saline|ns|sf|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica)\b", body):
                fluid_type = "normal saline"
            elif re.search(r"\b(?:ringer|ringers|lr)\b", body):
                fluid_type = "lactated Ringer's"
        return [{"type": "repeat_order", "target": target, "agent": agent, "fluid_type": fluid_type, "amount": value, "amount_unit": unit, "route": _route(body)}], verb
    reassess = verb in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar"}
    if reassess:
        delay, _ = _amount(body, r"minutes?|mins?|minutos?")
        if re.search(r"\b(?:hours?|horas?|seconds?|segundos?)\b", body):
            return [_clarification("Specify the reassessment interval in minutes.")], verb
        return [{"type": "reassessment", "delay_min": delay if delay is not None else 0}], verb

    # "Pido nefrostomia percutanea" is a request for urology, not for a study,
    # and the study dispatch owns the verb that introduced it. Asked before it,
    # so the service is reached rather than the refusal (2026-09-23).
    # Reading a result that is already back is not requesting the study again.
    # It had no way of being said at all until 2026-09-23: "revisa el lactato"
    # was refused, so the only way to see a result was to reorder the test.
    review = re.match(
        r"\s*(?:(?:me\s+)?(?:revisa|reviso|revisar|mira|miro|mirar|ve|veo|ver|lee|leo|leer|"
        r"revisemos|veamos|chequea|chequeo)\b|"
        r"(?:review|look\s+at|read|check)\b(?!\s+(?:the\s+)?(?:pulse|pressure|perfusion))|"
        r"(?:cu[aá]l\s+(?:es|fue)|qu[eé]\s+(?:muestra|dice|sali[oó]|result[oó]))\b|"
        r"(?:ya\s+)?(?:est[aá]|lleg[oó]|tengo)\s+(?:el|la|los|las)?\s*resultado)", body)
    if review:
        for name, pattern in _DIAGNOSTICS.items():
            if re.search(r"\b(?:" + pattern + r")\b", body[review.end():]):
                return [{"type": "result_review", "diagnostic": name}], verb or "review"

    # The x of xABCDE. A tourniquet, direct pressure and packing are the three
    # measures this engine performs, and each names where it is applied.
    bleeding = re.search(
        r"\b(?:torniquete|tourniquet|"
        r"(?:compresi[oó]n|presi[oó]n)\s+(?:directa|manual|externa)|direct\s+pressure|"
        r"empaquetamiento|packing|taponamiento|"
        r"(?:vendaje|ap[oó]sito)\s+(?:compresivo|hemost[aá]tico)|"
        r"(?:h[ae]mostatic|pressure)\s+dressing|control\s+de\s+(?:la\s+)?hemorragia|"
        r"h[ae]morrhage\s+control|bleeding\s+control)\b", body)
    if bleeding:
        measure = ("tourniquet" if re.search(r"torniquete|tourniquet", body)
                   else "packing" if re.search(r"empaquet|packing|taponamiento", body)
                   else "direct pressure")
        site = ("limb" if re.search(r"\b(?:extremidad|pierna|brazo|muslo|antebrazo|limb|leg|arm|thigh|"
                                    r"forearm|miembro)\b", body)
                else "wound")
        return [{"type": "hemorrhage_control", "measure": measure, "site": site}], verb or "apply"

    if re.search(r"\b(?:faja\s+p[eé]lvica|cintur[oó]n\s+p[eé]lvico|pelvic\s+binder|"
                 r"binder\s+p[eé]lvico|sabana\s+p[eé]lvica|pelvic\s+(?:sheet|wrap))\b", body):
        return [{"type": "pelvic_binder"}], verb or "apply"

    if re.search(r"\b(?:[aá]cido\s+tranex[aá]mico|tranexamic\s+acid|tranexamico|\btxa\b|"
                 r"exacyl|cyklokapron)\b", body):
        dose = re.search(r"(\d+(?:[.,]\d+)?)\s*(mg|g)\b", body)
        grams = None
        if dose:
            value = float(dose[1].replace(",", "."))
            grams = value / 1000 if dose[2] == "mg" else value
        return [{"type": "tranexamic_acid", "dose_g": grams, "route": _route(body) or "IV"}], verb or "give"

    if re.search(_SERVICE_PROCEDURE, body):
        return [{"type": "consult", "service": "urology"}], verb or "consult"

    # What a discharge is given with is part of the discharge, not a second
    # order: "de alta con control ambulatorio y criterios de reconsulta" held
    # the disposition the colic case is built around (2026-09-23).
    if re.match(r"(?:con\s+)?(?:criterios?\s+de\s+)?"
                r"(?:reconsulta|consulta\s+precoz|control\s+(?:ambulatorio|precoz|"
                r"con\s+\w+)|seguimiento|indicaciones|analgesia\s+oral|"
                r"return\s+precautions|safety\s+net(?:ting)?|follow[- ]up)\b", body):
        return [], None

    examined = _examination_order(body, verb)
    if examined is not None:
        if examined:
            return [{"type": "examination", "region": examined}], verb or "examine"
        # "Busco subir la presion" and "reviso diuresis y saturacion" share a verb
        # with the physical examination and are not one: the first is a goal, the
        # second names what the resident will watch. Neither is an order, and
        # asking which body part they meant stopped the encounter over language
        # the reasoning extractor already reads.
        if _is_reasoning(text):
            return [], None
        # Derived from the table above. Written out by hand it drifted: the
        # engine offered Extremities and this sentence never named it.
        named = [region.lower() for region, _ in _EXAMINATION_REGIONS]
        return [_clarification("Name the part of the examination to perform: "
                               + ", ".join(named[:-1]) + " or " + named[-1] + ".")], verb

    other_region = re.search(r"\b(?:abdomen|abdominal|pelvis|pelvic|spine|columna|craneo|skull|"
                             r"extremidad|extremity|limb|rodilla|knee|cadera|hip)\b", body)
    diagnostics = []
    for diagnostic, pattern in _DIAGNOSTICS.items():
        match = re.search(r"\b(?:" + pattern + r")\b", body)
        if diagnostic == "chest_xray" and other_region and not re.search(r"\btorax\b|\bchest\b", body):
            continue
        # A crossmatch is asked for without a study verb as often as with one
        # ("reservar 2 unidades", "grupo y pruebas cruzadas"). Only a verb that
        # gives the blood makes the sentence a transfusion instead.
        crossmatch = diagnostic == "crossmatch" and match and not _TRANSFUSING.search(body)
        if match and (verb in _DIAG_VERBS or crossmatch
                      or re.fullmatch(r"\s*(?:" + pattern + r")\s*\??", body)):
            diagnostics.append((match.start(), {"type": "diagnostic", "diagnostic": diagnostic}))
    if diagnostics:
        return [action for _, action in sorted(diagnostics, key=lambda x: x[0])], verb or "order"
    # Asking which gases is right when the resident asked for gases. "Los gases
    # muestran retencion de CO2" is a result they are reading, not an order, and
    # it held a whole escalation to non-invasive ventilation (2026-09-24).
    if re.search(r"\b(?:gases|gasometria|blood gases?)\b", body) and (
            verb in _DIAG_VERBS or re.fullmatch(r"\s*(?:(?:los|unos|the)\s+)?(?:gases|gasometria|blood gases?)\s*\??", body)):
        return [{'type': 'clarification', 'message': 'Specify arterial (ABG) or venous (VBG) blood gases.',
                 'pending_action': {'type': 'diagnostic', 'diagnostic': None}}], verb
    if re.search(r"\b(?:stress\s+test|exercise\s+(?:test|stress)|treadmill|test\s+de\s+esfuerzo|"
                 r"ergometr[ií]a|prueba\s+de\s+esfuerzo)\b", body):
        return [{"type": "stress_test"}], verb or "order"
    if verb in _DIAG_VERBS and verb not in {"order", "perform", "do", "realizar", "hacer"}:
        # "Control de PAM en 15 min" and "mido la saturacion" share a verb with a
        # study request and ask for neither: they name what the resident will
        # watch. Asking which study they meant held turns whose reassessment was
        # already stated (measured 2026-09-23).
        if _is_reasoning(text):
            return [], None
        # "Toma glibenclamida" and "toma betabloqueador" say what the patient
        # takes, which is history. "Tomar" is also how a sample is taken, so it
        # is read as a study only when what follows is not a medicine (2026-09-24,
        # two escalations held by the rehearsal of the twenty-scenario batch).
        if verb == "obtener" and _TAKES_MEDICATION.search(body):
            return [], None
        # "Pido 2 unidades de globulos rojos" asks the blood bank for units, and
        # whether to give them now or to have them reserved is the resident's to
        # say: "the study was not recognized" named neither (2026-09-24).
        if re.search(r"\b(?:unidades?|units?|u)\b", body) and re.search(
                r"\b(?:prbcs?|packed red (?:blood )?cells|blood|sangre|globulos rojos|hematies)\b", body):
            return [_clarification("Specify whether to transfuse these units now, with the number "
                                   "of units, or to request a crossmatch to have them reserved.")], verb
        return [_clarification("The requested study was not recognized. Specify one supported study per order.")], verb

    if not verb:
        shorthand = r"(?:sf|ns|suero\s+fisiologico|solucion\s+fisiologica|ringer(?:\s+lactato)?|lr|cristaloides?|synchronized cardioversion|synchronized shock|choque sincronizado|cardioversion|bipap|cpap|niv|vni|vmni|intubation|intubacion|bag[- ]mask|bag[- ]valve[- ]mask|bvm|ambu|oxygen|oxigeno|o2|nasal cann?ula|canula nasal|naricera|nc|non[- ]rebreather|nrb|room air|aire ambiente|dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|epinephrine|epinefrina|adrenaline|adrenalina|nitroglycerin|nitroglicerina|nitro|needle decompression|needle thoracostomy|finger thoracostomy|chest tube|thoracostomy|descompresion con aguja|descompresión con aguja|puncion pleural|punción pleural|tubo pleural|pleurotomia|pleurotomía)"
        medication_start = any(re.match(r"(?:" + pattern + r")\b", body) for agents in _AGENTS.values() for pattern in agents.values())
        quantity_start = bool(re.match(r"-?\d+(?:\.\d+)?\s*(?:mcg|ug|mg|g|ml|cc|l|units?|unidades?)\b", body))
        # A route written first is how the order is spoken in English: "IM
        # adrenaline 0.5 mg". The route is not the order, so it is stepped over
        # rather than made one.
        route_first = r"(?:im|iv|io|sc|ev|po|in)\s+"
        # A disposition written without a verb is still a disposition. "Alta con
        # analgesia oral y control en 7 dias" produced no action and no question
        # at all -- the closing decision of the encounter, lost in silence
        # (2026-09-23).
        if not (re.match(shorthand + r"\b", body) or medication_start or quantity_start
                or re.match(route_first + shorthand + r"\b", body)
                or re.match(r"(?:alta|discharge|hospitaliza|ingresa|traslada|admit|transfer)", body)):
            return [], None
        if re.search(r"\b(?:was|were|has been|had been|previously|already|caused|improved|worsened|fue|recibio|previamente|ya recibio|mejoro|empeoro)\b", body):
            return [], None

    medication_count = sum(bool(re.search(r"\b(?:" + pattern + r")\b", body)) for agents in _AGENTS.values() for pattern in agents.values())
    has_fluid = bool(re.search(r"\b(?:saline|ns|sf|ringer|ringers|lr|crystalloid|cristaloides?|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica)\b", body))
    if medication_count > 1 or (medication_count and has_fluid):
        return [_clarification("Separate each medication or fluid with its own dose and route so the order is unambiguous.")], verb

    if (re.search(r"\b(?:consult|call|consultar|interconsultar|llamar)\b", text)
            or re.search(_SERVICE_PROCEDURE, body) or verb in {"activate", "activar"}):
        service = None
        # The pulmonary embolism response team is asked for by its name here,
        # and the case declares involving it as what D3 turns on; only the
        # English acronym was listed (2026-09-23).
        for name, pattern in (("PERT", r"\bpert\b|equipo (?:de |para )?(?:respuesta )?"
                                       r"(?:de |a )?(?:tromboembolismo|tep|embolia pulmonar)"),
                              ("cardiology", r"cardiolog"), ("cath lab", r"cath(?:eterization)? lab|hemodinamia|hemodinamica"), ("gastroenterology", r"gastroenterolog|endoscop"),
                              # The service that decompresses an obstructed,
                              # infected kidney, asked for by its name or by what
                              # it is being asked to do (2026-09-23).
                              ("urology", r"urolog|nefrostom[ií]a|nephrostomy|"
                                          r"cat[eé]ter\s+doble\s+j|doble\s+j|double[- ]j|"
                                          r"ureteral\s+stent|stent\s+ureteral|"
                                          r"desobstru|descompresi[oó]n\s+(?:de\s+la\s+)?v[ií]a\s+urinaria"),
                              ("surgery", r"cirug[ií]a general|general surgery|cirujano"),
                              ("ICU", r"\bicu\b|\buci\b|intensive care|cuidados intensivos")):
            if re.search(pattern, body):
                service = name
                break
        return [{"type": "consult", "service": service}], verb
    # Faculty decision 2026-09-21: sending the patient home is a disposition of
    # its own, and it is the closing decision of the challenge that asks whether
    # the problem was addressed.
    if re.search(_DISCHARGE, body) or verb in {"discharge", "dar de alta"}:
        return [{"type": "disposition", "destination": "home"}], verb
    if verb in {"admit", "transfer", "hospitalizar", "ingresar", "trasladar"} and re.search(
            r"\bcath(?:eterization)?\s+lab\b|\bhemodinamia\b|\bhemodinamica\b|\bpabellon\s+de\s+hemodinamia\b", body):
        # "Lo traslado a hemodinamia" sends the patient to the cath lab, which is
        # what activating it does; it was held asking for a bed (2026-09-24).
        return [{"type": "consult", "service": "cath lab"}], verb
    if verb in {"admit", "transfer", "hospitalizar", "ingresar", "trasladar"}:
        # The coronary unit is a cardiovascular critical-care bed under all its
        # names, and "UCO" is how it is asked for here (faculty, 2026-09-21).
        destination = "coronary care unit" if re.search(_CORONARY_UNIT, body) else None
        # "UPC" is what a critical-care bed is called here; the unit that takes
        # this patient is the intensive one (2026-09-22, playing the generated
        # cardiogenic shock case, where the order was held asking for a name the
        # resident had already given).
        if destination is None and re.search(r"\b(?:icu|uci|upc)\b|intensive care|cuidados intensivos|"
                                             r"unidad de paciente critico|paciente critico", body):
            destination = "ICU"
        if re.search(r"\bward\b|\bsala\b|hospital ward", body):
            destination = "ward"
        # "Unidad de tratamiento intermedio" is the other half of the UPC. The
        # bare "UTI" is deliberately absent: in English it is an infection.
        if destination is None and re.search(r"step[- ]down|intermediate care|intermedios?\b|\bui\b|"
                                             r"unidad de cuidados intermedios|"
                                             r"(?:unidad de )?tratamiento intermedio", body):
            destination = "intermediate care"
        if destination is None:
            return [_clarification("Specify where the patient is admitted or transferred: the ICU, the "
                                   "coronary care unit, intermediate care, the ward, or home.")], verb
        return [{"type": "disposition", "destination": destination}], verb
    if verb in {"cardiovert", "cardiovertir", "cardiovierto"} or re.search(r"\b(?:cardioversion|synchronized shock|choque sincronizado)\b", body):
        if re.search(r"\b(?:unsynchronized|defibrillation|no sincronizado)\b", body):
            return [_clarification("Specify synchronized cardioversion; defibrillation is outside this pulse-present encounter.")], verb
        energy, _ = _amount(body, r"j|joules?|julios?")
        return [{"type": "cardioversion", "energy_j": energy, "synchronized": True}], verb
    if (_operation(verb) in {"adjust", "continue"}
            and re.search(r"\b(?:ventilator|ventilation|ventilador|ventilacion\s+mecanica|"
                          r"fio2|peep|ipap|epap|vc[/ -]?ac|pc[/ -]?ac|"
                          r"tidal\s+volume|volumen\s+corriente|vt)\b", body)
            and not re.search(r"\b(?:bipap|cpap|niv|vni|vmni)\b", body)):
        if re.search(r"\b(?:by|en)\s+-?\d", body):
            return [_clarification("Specify absolute target ventilator settings, not a relative change.")], verb
        modes = [mode for mode, pattern in (("VC/AC", _VC_MODE), ("PC/AC", _PC_MODE)) if re.search(pattern, body)]
        if len(modes) > 1:
            return [_clarification("Specify one target ventilator mode.")], verb
        return [{"type": "respiratory_adjustment", "operation": _operation(verb),
                 "ventilator_mode": modes[0] if modes else None,
                 "fio2_percent": _settings(body, "fio2"), "peep_cmh2o": _settings(body, "peep"),
                 "ipap_cmh2o": _settings(body, "ipap"), "epap_cmh2o": _settings(body, "epap"),
                 **_ventilator_extras(body)}], verb
    if re.search(r"\b(?:naloxone|naloxona|narcan)\b", body) and re.search(
            r"\b(?:infusion|infusi[oó]n|drip|goteo|per\s+hour|/\s*h(?:r|our)?\b|por\s+hora)\b", body):
        rate = re.search(r"(-?\d+(?:\.\d+)?)\s*(mg|mcg|ug)\s*(?:/|\s+(?:per|por|cada)\s+)\s*(?:h|hr|hour|hora)\b", body)
        milligrams = None
        if rate:
            milligrams = float(rate[1]) / 1000 if rate[2] in {"mcg", "ug"} else float(rate[1])
        return [{"type": "naloxone_infusion", "rate_mg_h": milligrams, "operation": _operation(verb)}], verb or "start"
    if re.search(r"\b(?:d10|d\s*10|dextrose\s*10|glucosa(?:do)?\s*(?:al\s*)?10|suero\s+glucosado)\b", body):
        rate = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:ml|cc)\s*(?:/|\s+(?:per|por|cada)\s+)\s*(?:h|hr|hour|hora)\b", body)
        return [{"type": "dextrose_infusion", "rate_ml_h": float(rate[1]) if rate else None,
                 "concentration_percent": 10, "operation": _operation(verb)}], verb or "start"
    if re.search(r"\b(?:oral\s+(?:glucose|carbohydrate|sugar)|glucose\s+gel|juice|zumo|jugo|"
                 r"carbohidrato\s+oral|glucosa\s+oral|az[uú]car\s+oral|comida|colaci[oó]n)\b", body):
        return [{"type": "oral_carbohydrate"}], verb or "give"
    if re.search(r"\b(?:stress\s+test|exercise\s+(?:test|stress)|treadmill|test\s+de\s+esfuerzo|"
                 r"ergometr[ií]a|prueba\s+de\s+esfuerzo)\b", body):
        return [{"type": "stress_test"}], verb or "order"
    if re.search(r"\b(?:thromboly\w*|fibrinoly\w*|trombolisis|trombol[ií]tico\w*|fibrinol[ií]tico\w*)\b", body) \
            and not any(re.search(r"\b(?:" + pattern + r")\b", body) for pattern in _AGENTS["thrombolysis"].values()):
        return [_clarification("Specify the thrombolytic agent and dose, for example tenecteplase 40 mg IV.")], verb
    if re.search(r"\b(?:needle\s+decompress\w*|needle\s+thoracostomy|finger\s+thoracostomy|chest\s+tube|"
                 r"thoracostomy|tube\s+thoracostomy|descompresi[oó]n\s+con\s+aguja|punci[oó]n\s+(?:pleural|descompresiva)|"
                 r"tubo\s+(?:pleural|de\s+t[oó]rax)|pleurotom[ií]a)\b", body):
        side = "left" if re.search(r"\b(?:left|izquierd\w*)\b", body) else "right"
        tube = bool(re.search(r"\b(?:chest\s+tube|thoracostomy|tubo|pleurotom[ií]a)\b", body))
        return [{"type": "chest_decompression", "side": side, "device": "chest tube" if tube else "needle"}], verb or "perform"
    if (verb in {"disconnect", "desconectar", "desconecta", "desconecto"}
            or re.search(r"\b(?:disconnect\w*|desconect\w*)\b", body)) and re.search(
            r"\b(?:circuit|ventilator|tubing|circuito|ventilador|tubuladura|tube|tubo)\b", body):
        return [{"type": "ventilator_disconnect"}], verb or "disconnect"
    # "Subele la infusion a 100 mcg/min": the resident names the running
    # treatment by its role. The engine resolves which one, and refuses when
    # there is none or more than one, exactly as it does for a ventilator.
    if (_operation(verb) in {"adjust", "continue", "stop"}
            and re.search(r"\b(?:infusion|drip|goteo|bomba)\b", body)
            and not re.search(_NAMED_INFUSION, body)):
        rate, units = _amount(body, r"mcg\s*/\s*kg\s*/\s*min|mcg\s*/\s*min|ug\s*/\s*kg\s*/\s*min|ug\s*/\s*min|ml\s*/\s*h(?:r|ora)?")
        return [{"type": "infusion_adjustment", "operation": _operation(verb),
                 "rate_value": rate, "rate_units": units}], verb
    # Faculty decision 13 of 2026-09-21: the nursing and support orders a
    # resident writes without thinking are part of the encounter. They are
    # recorded with a state of their own and they change no physiology.
    support = _support_order(body, verb)
    if support is not None:
        return [support], verb
    if re.search(_PACING, body):
        operation = _operation(verb) or "start"
        if operation == "adjust" and not re.search(r"\b(?:marcapaso|pacing|pacer)", body):
            operation = "adjust"
        rate, _ = _amount(body, r"(?:latidos?\s*)?(?:por|/)\s*min(?:uto)?|lpm|bpm|beats?\s*/\s*min")
        if rate is None:
            match = re.search(r"\b(?:a|at|rate|frecuencia|de)\s+(\d+(?:\.\d+)?)(?![\d.])(?!\s*(?:ma\b|miliamp|milliamp))", body)
            rate = float(match[1]) if match else None
        current, _ = _amount(body, r"ma\b|miliamperios?|miliamperes?|milliamps?|milliamperes?")
        return [{"type": "transcutaneous_pacing", "operation": "stop" if operation == "stop" else operation,
                 "rate_per_min": rate, "output_ma": current}], verb
    if re.search(r"\b(?:bag[- ]mask|bag[- ]valve[- ]mask|bvm|ambu|"
                 r"bolsa[- ](?:mascarilla|mascara)|bolsa valvula (?:mascarilla|mascara)|"
                 r"bolsa de reanimacion|ventilacion manual|ventilar a mano)\b", body):
        return [{"type": "bag_mask"}], verb
    if ((verb in {"intubate", "intubar", "intubo"} or re.match(r"(?:intubation|intubacion)\b", body))
            # A clause that only names a drug is that drug's order, even when it
            # follows an intubation and inherits its verb (2026-09-21).
            and not (_names_an_airway_drug(body) and not _AIRWAY_CONTEXT.search(body))):
        mode = "VC/AC" if re.search(_VC_MODE, body) else "PC/AC" if re.search(_PC_MODE, body) else None
        if re.search(r"\bpc[/ -]?ac\b|pressure control|control presion", body):
            mode = "PC/AC"
        airway = {"type": "intubation", "ventilator_mode": mode, "fio2_percent": _settings(body, "fio2"),
                  "peep_cmh2o": _settings(body, "peep"), **_ventilator_extras(body)}
        # A rapid sequence names its drugs in the same sentence as the procedure.
        # Each one is confirmed as its own order instead of disappearing into the
        # airway (faculty decision 11, 2026-09-21).
        drugs = []
        for kind in ("procedural_sedation", "neuromuscular_blockade"):
            for agent, pattern in _AGENTS[kind].items():
                if re.search(r"\b(?:" + pattern + r")\b", body):
                    drug = _medication(body, kind, agent)
                    # The drugs of a rapid sequence go into a vein; the route is
                    # not a question worth holding the airway over.
                    if isinstance(drug, dict) and drug.get("route") is None:
                        drug["route"] = "IV"
                    drugs.append(drug)
                    break
        return [airway, *drugs], verb
    if re.search(r"\b(?:bipap|cpap|niv|vni|vmni|non[- ]invasive ventilation|ventilacion (?:mecanica )?no invasiva)\b", body):
        mode = "CPAP" if re.search(r"\bcpap\b", body) else "BiPAP" if re.search(r"\bbipap\b", body) else None
        ipap, epap = _settings(body, "ipap"), _settings(body, "epap")
        pair = re.search(r"\bbipap\s+(?:at\s+|a\s+)?(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", body)
        if pair and ipap is None and epap is None:
            ipap, epap = float(pair[1]), float(pair[2])
        cpap = re.search(r"\bcpap\s+(?:at\s+|a\s+)?(\d+(?:\.\d+)?)", body)
        if cpap and epap is None:
            epap = float(cpap[1])
        return [{"type": "niv", "mode": mode, "ipap_cmh2o": ipap, "epap_cmh2o": epap, "fio2_percent": _settings(body, "fio2"), "operation": _operation(verb)}], verb
    if re.search(r"\b(?:dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro|epinephrine|epinefrina|adrenaline|adrenalina|epi)\b", body):
        kind = ("epinephrine" if re.search(r"\b(?:epinephrine|epinefrina|adrenaline|adrenalina|epi)\b", body)
                else "nitroglycerin" if re.search(r"\b(?:nitroglycerin|nitroglicerina|nitro)\b", body)
                else "dobutamine" if re.search(r"\b(?:dobutamine|dobutamina)\b", body) else "norepinephrine")
        # A rate may be written with a slash or in words: "20 mcg/min",
        # "20 mcg per minute", "20 mcg por minuto".
        per = r"(?:\s*/\s*|\s+(?:per|por|each|every|cada|a\s+la|al)\s+)"
        rate_matches = list(re.finditer(
            r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(mcg|ug|mg)" + per + r"(kg" + per + r")?"
            r"(min(?:ute)?s?|minutos?|h(?:r|our)?s?|horas?)\b", body))
        if len(rate_matches) > 1 or (_operation(verb) == "adjust" and re.search(r"\b(?:by|en)\s+-?\d", body)):
            return [_clarification("Specify a single absolute target infusion rate; a relative change or several rates is ambiguous.")], verb
        rate_match = rate_matches[0] if rate_matches else None
        rate, units = None, None
        # A bolus, push, sublingual dose or a mass with no time unit is a single
        # dose, not an infusion rate. It used to fall through to the bare-number
        # fallback, so "nitroglycerin 600 mcg IV bolus" started an infusion at
        # 600 mcg/min. This engine runs these drugs only as continuous infusions,
        # so say so and convert nothing.
        name = {"nitroglycerin": "Nitroglycerin", "dobutamine": "Dobutamine",
                "epinephrine": "Epinephrine"}.get(kind, "Norepinephrine")
        single_dose = re.search(
            r"\b(?:bolus|bolo|push|stat\s+dose|sublingual|sublingual|sl|spray|tablet|tableta|comprimido|"
            r"pastilla|dosis\s+unica|dosis\s+única)\b", body)
        mass_dose = None if rate_match else re.search(
            r"(?<![\w.])((?:\d+(?:\.\d+)?|\.\d+))\s*(mcg|ug|mg)\b(?!\s*/)", body)
        # The intramuscular dose of anaphylaxis. Until 2026-09-23 this fell
        # through to "this engine runs these drugs only as continuous
        # infusions", so the one order the specialty is most insistent about was
        # refused. The route is the order here, not a detail of it.
        intramuscular = re.search(
            r"\b(?:im|intramuscular(?:ly|es)?|intramuscul[ao]r|"
            r"sc|subcutaneous(?:ly)?|subcut[aá]ne[ao]|"
            r"muslo|thigh|vasto\s+lateral|vastus\s+lateralis|deltoides|deltoid)\b", body)
        if kind == "epinephrine" and not rate_match and mass_dose and intramuscular:
            milligrams = float(mass_dose[1]) / (1000 if mass_dose[2] in {"mcg", "ug"} else 1)
            route = "SC" if re.search(r"\b(?:sc|subcutaneous(?:ly)?|subcut[aá]ne[ao])\b", body) else "IM"
            return [{"type": "epinephrine_im", "dose_mg": milligrams, "route": route}], verb or "give"
        if kind == "epinephrine" and not rate_match and mass_dose and (
                single_dose or re.search(r"\b(?:iv|ev|intravenous|intravenos[ao])\b", body)):
            # Diluted epinephrine is also given as small IV boluses (50-150 mcg).
            dose = float(mass_dose[1]) * (1000 if mass_dose[2] == "mg" else 1)
            return [{"type": "epinephrine_bolus", "dose_mcg": dose, "route": "IV"}], verb
        if (kind == "nitroglycerin" and not rate_match and mass_dose
                and not re.search(r"\b(?:sublingual|sl|spray|tablet|tableta|comprimido|pastilla)\b", body)
                and (single_dose or re.search(r"\b(?:iv|ev|intravenous|intravenos[ao])\b", body))):
            # An IV nitroglycerin bolus (typically 1000-2000 mcg) is a treatment of its own.
            dose = float(mass_dose[1]) * (1000 if mass_dose[2] == "mg" else 1)
            return [{"type": "nitroglycerin_bolus", "dose_mcg": dose, "route": "IV"}], verb
        if not rate_match and (single_dose or mass_dose):
            form = single_dose[0].lower() if single_dose else "single dose"
            form = {"sl": "sublingual dose", "sublingual": "sublingual dose", "bolo": "bolus",
                    "push": "IV push", "spray": "spray dose", "tableta": "tablet",
                    "comprimido": "tablet", "pastilla": "tablet", "stat dose": "single dose",
                    "dosis unica": "single dose", "dosis única": "single dose"}.get(form, form)
            dose = f" of {mass_dose[1]} {mass_dose[2]}" if mass_dose else ""
            unit = "mcg/min" if kind == "nitroglycerin" else "mcg/kg/min or mcg/min"
            return [{**_clarification(
                f"{name} was understood as {'an' if form[0] in 'aeiouAEIOU' else 'a'} {form}{dose}. "
                + (f"This encounter gives nitroglycerin as a continuous IV infusion or an IV bolus, so nothing was "
                 f"converted or executed. To give it, state an infusion rate in {unit} or an IV bolus in mcg, or say cancel."
                 if kind == "nitroglycerin" else
                 f"This encounter gives {name.lower()} only as a "
                 f"continuous IV infusion, so nothing was converted or executed. To give it, state an "
                 f"infusion rate in {unit}, or say cancel.")),
                "unsupported_administration": {"agent": kind, "form": form,
                                               "dose": float(mass_dose[1]) if mass_dose else None,
                                               "units": mass_dose[2] if mass_dose else None}}], verb
        if not rate_match:
            bare_rates = re.findall(r"(?<![\w.])(-?(?:\d+(?:\.\d+)?|\.\d+))(?![\w.])", body)
            if len(bare_rates) == 1 and not re.search(r"\b(?:minutes?|mins?|hours?|horas?|minutos?)\b", body):
                rate = float(bare_rates[0])
        if rate_match:
            rate = float(rate_match[1]) * (1000 if rate_match[2] == "mg" else 1)
            if rate_match[4].startswith("h"):
                rate /= 60
            units = "mcg/kg/min" if rate_match[3] else "mcg/min"
        if kind == "nitroglycerin":
            if units == "mcg/kg/min":
                return [_clarification("Specify nitroglycerin as an absolute infusion rate in mcg/min.")], verb
            return [{"type": kind, "rate_mcg_min": rate, "operation": _operation(verb)}], verb
        return [{"type": kind, "rate": rate, "units": units, "operation": _operation(verb)}], verb
    if re.search(_OXYGEN_MENTION, body):
        return [_oxygen_order(body, verb)], verb
    if re.search(r"\b(?:prbcs?|packed red (?:blood )?cells|blood|sangre|globulos rojos|concentrad[oa]s? de hematies|hematies)\b", body):
        units, _ = _amount(body, r"units?|unidades?|u")
        return [{"type": "blood", "units": units}], verb
    if re.search(r"\b(?:saline|normal saline|ns|sf|sf|ringer|lactated ringers?|lr|crystalloid|cristaloides?|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica|sueros?|fluid|fluids|volumen)\b", body):
        if _operation(verb) == "stop":
            # "Stop the normal saline" ends a running infusion; it is not a new bolus.
            fluid_type = ("normal saline" if re.search(r"\b(?:saline|ns|sf|salino|fisiologico|fisiologica)\b", body)
                          else "lactated Ringer's" if re.search(r"\b(?:ringer|ringers|lr)\b", body) else None)
            return [{"type": "fluid", "operation": "stop", "fluid_type": fluid_type}], verb
        volume, units = _amount(body, r"ml|cc|lts?|liters?|litres?|litros?|l")
        if volume is not None and units not in {"ml", "cc"}:
            volume *= 1000
        if volume is None:
            # Reuse the earlier branch's named-fluid shorthand and word volumes.
            # Never use its first-match fallback to resolve conflicting quantities.
            numbers = re.findall(r"(?<![\w.])(?:\d+(?:\.\d+)?|\.\d+)", body)
            if len(numbers) <= 1 and not re.search(r"-\s*\d|/\s*(?:min|h|hr)", body):
                volume = parse_volume_ml(body)
        fluid_type = None
        if re.search(r"\b(?:saline|ns|sf|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica)\b", body):
            fluid_type = "normal saline"
        elif re.search(r"\b(?:ringer|ringers|lr)\b", body):
            fluid_type = "lactated Ringer's"
        elif re.search(r"\b(?:crystalloid|cristaloides?)\b", body):
            fluid_type = "crystalloid"
        fluid = {"type": "fluid", "volume_ml": volume, "fluid_type": fluid_type}
        # A stated route is kept so the engine can confirm it; none is assumed.
        route = _route(body)
        if route:
            fluid["route"] = route
        return [fluid], verb

    # Continuous nebulized beta-agonist: a rate per hour, or the word continuous.
    # "Suspende la nebulizacion continua" names the therapy without naming the
    # drug, which is how it is stopped and titrated at the bedside.
    named_therapy = re.search(r"\b(?:continuous\s+nebuli[sz](?:er|ation|ed\s+treatment)|"
                              r"nebulizaci[oó]n\s+continua|nebulizador\s+continuo)\b", body)
    if re.search(r"\b(?:albuterol|salbutamol)\b", body) or named_therapy:
        continuous = named_therapy or re.search(
            r"\b(?:continuous|continuously|continua|continuo|continuamente|"
            r"sin\s+interrupci[oó]n|back[- ]to[- ]back)\b", body)
        hourly = re.search(r"(\d+(?:\.\d+)?)\s*mg\s*(?:/|\s+(?:per|por|cada|a\s+la)\s+)\s*(?:h|hr|hour|hora)\b", body)
        if continuous or hourly:
            operation = _operation(verb)
            rate = float(hourly[1]) if hourly else (None if operation == "stop" else CONTINUOUS_NEBULIZER_MG_PER_H)
            return [{"type": "continuous_bronchodilator", "agent": "albuterol",
                     "rate_mg_h": rate, "route": "nebulized", "operation": operation}], verb or "start"

    medicines = []
    for kind, agents in _AGENTS.items():
        for agent, pattern in agents.items():
            match = re.search(r"\b(?:" + pattern + r")\b", body)
            if match:
                medicines.append((match.start(), kind, agent))
    if len(medicines) > 1:
        return [_clarification("Separate each medication with its own dose and route so the order is unambiguous.")], verb
    if medicines:
        _, kind, agent = medicines[0]
        # A bare drug name is only an order with an explicit command or dose.
        if verb or re.search(r"\d\s*(?:mcg|ug|mg|g|units?|ui)\b", body):
            if _operation(verb) == "continue":
                # "Manten la heparina" is a decision not to change anything. The
                # engine answers with what is already recorded instead of holding
                # the turn over a dose the resident did not intend to give.
                return [{"type": kind, "agent": agent, "operation": "continue"}], verb
            if _operation(verb) != "start":
                # A sedation or analgesia infusion is a running order: it is
                # titrated and stopped like any other (faculty decision 11).
                if kind in _WEIGHT_BASED and (_operation(verb) == "stop" or _INFUSION_RATE.search(body)):
                    infusion = _medication(body, kind, agent)
                    if infusion.get("type") == "sedation_infusion":
                        return [{**infusion, "operation": _operation(verb)}], verb
                    return [{"type": "sedation_infusion", "agent": agent, "rate": None,
                             "units": None, "route": _route(body) or "IV",
                             "operation": _operation(verb)}], verb
                return [_clarification("This fixed-dose medication order needs an explicit new dose; stopping it is not a supported new administration.")], verb
            medication_text = body + " nebulized" if verb in {"nebulize", "nebulizar"} else body
            return [_medication(medication_text, kind, agent)], verb or "give"
    if verb:
        # A goal or an expectation is not an unreadable order. It carries no
        # dose, and quoting it back as one held turns whose reasoning was
        # complete (measured 2026-09-23).
        if _is_reasoning(text):
            return [], None
        # The rest of the submission is held rather than discarded.
        return [_unreadable(piece)], verb
    return [], None


def _parse_piece(piece, inherited=None):
    dose_piece = re.sub(r"\b(?:over|durante|en)\s+\d+(?:\.\d+)?\s*(?:minutes?|mins?|minutos?|hours?|horas?|seconds?|segundos?)\b", "", piece)
    if re.search(r"\b(?:reassess|reevaluar|reevaluo|revalorar|reassessment)\b", piece):
        dose_piece = piece
    actions, verb = _parse_piece_core(dose_piece, inherited)
    # An unknown verb is not a reason to lose a treatment. Found by playing the
    # pneumonia case in Spanish: "Pasa 1000 mL de suero fisiologico IV" produced
    # no action and no question at all, and the patient simply never received the
    # litre. A clause that names both a substance and a quantity that can only be
    # administered is quoted back, so an unread order costs a turn, not a
    # treatment. A withheld order ("no le pases volumen") is not one of these.
    if (not actions and not verb and not _NEGATION.match(str(piece).strip())
            and not _REPORTS_OR_WITHHOLDS.search(dose_piece)
            and _ADMINISTERED_QUANTITY.search(dose_piece) and _names_a_substance(dose_piece)):
        return [_unreadable(piece)], None
    # Delivery time is attached to this treatment clause, never to reasoning or
    # the reassessment clause. Retain unsupported/ambiguous timing as a question.
    text = _NON_ORDER.split(piece, maxsplit=1)[0]
    matches = list(re.finditer(r"\b(?:over|durante|en)\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|minutos?|hours?|horas?|seconds?|segundos?)\b", text))
    # A disposition or a consult has no delivery time: "de alta con control en 24
    # horas" states when the patient is seen again, not how long an order runs.
    treatments = [a for a in actions if a['type'] not in {'diagnostic', 'reassessment', 'clarification',
                                                          'disposition', 'consult', 'reperfusion_referral'}]
    if matches and treatments:
        if len(matches) != 1 or len(treatments) != 1:
            return [_clarification("Specify one delivery duration for each treatment.")], verb
        value, unit = float(matches[0][1]), matches[0][2]
        value *= 60 if unit.startswith(('hour', 'hora')) else 1 / 60 if unit.startswith(('second', 'segundo')) else 1
        treatments[0]['administration_duration_min'] = value
    return actions, verb


# Verbs that also state a goal: "and increase perfusion" is reasoning, whereas
# "and increase FiO2 to 80%" is an order.
_GOAL_VERBS = {"increase", "decrease", "lower", "raise", "titrate", "continue", "aumentar", "aumento",
               "disminuir", "disminuyo", "titular", "continuar", "mantener"}
_PHYSIOLOGICAL_OBJECT = re.compile(
    r"(?:(?:the|her|his|el|la|los|las|su)\s+)?(?:preload|afterload|perfusion|oxygenation|ventilation|"
    r"blood pressure|bp|map|pressure|heart rate|work of breathing|congestion|oxygen delivery|demand|"
    r"precarga|poscarga|postcarga|presion|pa|pas|pam|oxigenacion|ventilacion|frecuencia|trabajo|"
    r"congestion|demanda|consumo|entrega)\b"
)
_REASSESS_VERBS = {"reassess", "re-assess", "reevaluate", "recheck", "reevaluar", "reevaluo", "revalorar"}
_CLAUSE_BOUNDARY = re.compile(r"\s*,\s*(?:(?:and|y|then|luego)\s+)?|\s+(?:and|y|then|luego)\s+")


def _order_after_reasoning(text):
    """Return the orders that follow a statement of reasoning in one sentence.

    "My priority is perfusion, give 1000 mL NS" states a priority and then gives
    an order. The reasoning is captured elsewhere; the order must still be
    executed. A later clause counts only when it opens with an order verb, so
    "and reducing preload" or "y bajar precarga" remain part of the reasoning.
    """
    for boundary in _CLAUSE_BOUNDARY.finditer(text):
        rest = text[boundary.end():]
        command = _COMMAND.match(rest)
        if not command:
            continue
        if command["verb"] in _GOAL_VERBS and _PHYSIOLOGICAL_OBJECT.match(rest[command.end():]):
            continue
        # "My priority is to restore glucose and reassess the patient" states an
        # intention; only a timed reassessment ("reassess in 30 minutes") schedules one.
        if command["verb"] in _REASSESS_VERBS and not re.search(r"\d", rest):
            continue
        # "check for early fluid overload" or "get the right level of care" is still
        # reasoning: the clause counts only if it names an order the parser knows.
        first = re.split(r"\s*(?:,|\+|\band\b|\by\b|\be\b(?=\s+[a-z])|\bthen\b|\bluego\b)\s*", rest, maxsplit=1)[0]
        parsed, _ = _parse_piece(first)
        if not any(action["type"] != "clarification" for action in parsed):
            continue
        return rest
    return None


def parse_family_actions(text) -> dict:
    """Return source-ordered action dictionaries without changing patient state.

    Semicolons, full stops, and newlines end conditional/negated scope. Commas,
    ``and``/``y`` and ``+`` can chain orders and inherit an explicit order verb.
    A conditional instruction is retained as a future plan, never executed now.
    """
    raw = str(text or "")
    normalized = _spanish_imperatives(
        _spanish_proclitics(_declared_intention(_normalize(raw))))
    # A resident who says to wait for a result before treating has said
    # something about sequence that the engine must not optimise away (faculty
    # specification 2026-09-23, section 5). The two halves are parsed
    # separately and the second half is marked as waiting on the first.
    held_until, normalized = _sequenced(normalized)
    actions, future = [], []
    queue = re.split(r"[;\n]+|(?<!\d)\.(?!\d)|(?<=\d)\.(?!\d)", normalized)
    while queue:
        sentence = queue.pop(0).strip()
        if not sentence:
            continue
        # A priority/expected-response statement is a description of reasoning.
        # Only a later clause that opens with an order verb is read as an order.
        if _NON_ORDER.match(sentence):
            sentence = _order_after_reasoning(sentence)
            if not sentence:
                continue
        rationale = _NON_ORDER.search(sentence)
        if rationale:
            following = _order_after_reasoning(sentence[rationale.start():])
            if following:
                queue.insert(0, following)
            sentence = sentence[:rationale.start()].strip(" ,")
            if not sentence:
                continue
        conditional = _CONDITIONAL.search(sentence)
        if conditional:
            # "Start oxygen ..., and if BP falls give fluids" contains an
            # unconditional first order. "Give oxygen if sats fall" does not.
            boundary = next((match for match in re.finditer(r"(?:,\s*)?\b(?:and|y|then|luego)\s+", sentence)
                             if match.end() == conditional.start()), None)
            # Safety-netting advice carries its own condition, and the order it
            # follows is not conditional on it: "la envio a su casa con
            # indicacion de volver si se repite" is a discharge that happened,
            # plus advice about what would bring her back. Read as one
            # conditional, the disposition vanished in silence -- and a
            # discharge is the trigger of two defined critical events, so the
            # event went with it (2026-09-23).
            advice = (None if boundary else
                      _ADVICE_CLAUSE.search(sentence[:conditional.start()]))
            if advice:
                future.append(sentence[advice.start():])
                # The conjunction that introduced the advice goes with it.
                sentence = re.sub(r"(?:,\s*)?\b(?:and|y|then|luego)\s*$", "",
                                  sentence[:advice.start()].strip(" ,")).strip(" ,")
                if not sentence:
                    continue
            elif boundary:
                future.append(sentence[conditional.start():])
                sentence = sentence[:boundary.start()].strip(" ,")
                if not sentence:
                    continue
            else:
                if _COMMAND.search(re.sub(r"^.*?[, :]", "", sentence)) or re.search(r"\b(?:give|dar|administrar|start|iniciar|order|solicitar|reassess|reevaluar)\b", sentence):
                    future.append(sentence)
                continue
        inherited = None
        negated = False
        # Do not split the clinical device name "bag and mask", nor the blood
        # bank's two-word requests: "grupo" alone is not a study (2026-09-24).
        sentence = re.sub(r"\bbag and mask\b", "bag-mask", sentence)
        sentence = re.sub(r"\bgrupo y (?=pruebas cruzadas|rh\b|factor)", "grupo_y_pruebas ", sentence)
        sentence = re.sub(r"\btype and (?=screen|cross)", "type_and_", sentence)
        sentence = re.sub(r"\btype_and_(?:screen|cross(?:match)?)\b", "type_and_screen", sentence)
        pieces = re.split(r"\s*(?:,|\+|\band\b|\by\b|\be\b(?=\s+[a-z])|\bthen\b|\bluego\b)\s*", sentence)
        # Ventilator settings written naturally ("intubate, VC/AC, FiO2 100% and
        # PEEP 5") belong to the airway order, not to separate orders.
        merged = []
        for piece in pieces:
            candidate = piece
            if merged and re.search(_PACING, merged[-1]) and _PACING_SETTING.match(piece):
                merged[-1] += " " + piece
                continue
            if merged and _AIRWAY_PLACEMENT.search(merged[-1]):
                # "Intuba y conectalo a ventilacion mecanica en VC/AC con FiO2
                # 100%" is one airway order spoken the way it is spoken. Read as
                # two, the settings were lost and "volumen corriente 6 mL/kg"
                # became a 6 mL fluid bolus (asthma case, 2026-09-21).
                without_verb = _CONNECTED_SUPPORT.sub("", piece, count=1).strip()
                if without_verb and without_verb != piece and _VENTILATION_SETTING.match(without_verb):
                    candidate = without_verb
            if merged and _VENTILATION_SETTING.match(candidate):
                # Settings belong to the airway order even when the induction
                # drugs of a rapid sequence were written between them.
                target = (len(merged) - 1 if _VENTILATION_ORDER.search(merged[-1])
                          else next((i for i in range(len(merged) - 1, -1, -1)
                                     if _AIRWAY_PLACEMENT.search(merged[i])), None))
                if target is not None:
                    merged[target] += " " + candidate
                    continue
            merged.append(piece)
        pieces = merged
        grouped = []
        index = 0
        while index < len(pieces):
            piece = pieces[index]
            command = _COMMAND.match(piece)
            if command and (command["verb"] in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar"} or (command["verb"] in {"monitor", "assess", "check", "recheck", "measure", "medir", "mido", "controlar", "control", "vigilar", "monitorizar"} and re.search(r"\b(?:blood pressure|heart rate|respiratory rate|oxygen saturation|o2 saturation|spo2|saturacion|presion arterial|perfusion|mental status)\b", piece)) or re.match(r"continue monitoring\b", piece)):
                while index + 1 < len(pieces) and not (_COMMAND.match(pieces[index + 1]) or _NON_ORDER.match(pieces[index + 1]) or _NEGATION.match(pieces[index + 1])):
                    # A named study in a check/monitor list remains a separate
                    # requested investigation rather than disappearing into vitals.
                    if command["verb"] not in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar"} and any(re.search(r"\b(?:" + pattern + r")\b", pieces[index + 1]) for pattern in _DIAGNOSTICS.values()):
                        break
                    index += 1
                    piece += ", " + pieces[index]
            grouped.append(piece)
            index += 1
        reasoning_head = False
        for piece in grouped:
            if not piece:
                continue
            if _NEGATION.match(piece):
                negated = True
                inherited = None
                continue
            explicit = _COMMAND.match(piece)
            if negated and not explicit:
                continue
            if explicit:
                negated = False
            if _NON_ORDER.match(piece):
                reasoning_head = True
                inherited = None
                continue
            if _UNMODELED_ORDER.search(piece):
                # Recognised and not something this version executes: said back
                # as "recognised but not executed in this build", recorded with
                # the decision, and the other orders run (2026-09-24, the same
                # rule the faculty set for a study the simulator does not model).
                future.append(piece.strip())
                inherited = None
                continue
            parsed, inherited = _parse_piece(piece, inherited)
            if (reasoning_head and len(parsed) == 1 and parsed[0].get("type") == "clarification"
                    and str(parsed[0].get("message", "")).startswith("The requested study")):
                # The rest of a stated priority is not a request for a study.
                inherited = None
                continue
            actions.extend(parsed)
    actions = _one_sample_each(actions)
    if held_until:
        deferred = parse_family_actions(held_until)
        study = next((a["diagnostic"] for a in actions if a.get("type") == "diagnostic"), None)
        for action in deferred["actions"]:
            if action.get("type") in {"clarification", "reassessment"}:
                continue
            # What it waits for: the study named in the same entry when there is
            # one, and otherwise every result that is still out.
            action["after_result"] = study or "any_pending"
            actions.append(action)
        future.extend(deferred.get("recognized_future_actions", []))
    return {"raw_text": raw, "actions": actions, "recognized_future_actions": future}


_LEAD_STUDIES = ("ecg_right", "ecg_posterior")


def _one_sample_each(actions):
    """One submission that names a panel twice orders it once.

    "Electrolitos, funcion renal y hemograma" names the same basic panel twice,
    and the held order read back "Laboratory results + Laboratory results"
    (2026-09-21). Two samples drawn in the same minute are one sample.
    """
    # One submission that asks twice for the same support asks once.
    support, unique = set(), []
    for action in actions:
        kind = action.get("type")
        if kind in {"vascular_access", "monitoring", "npo", "urinary_catheter", "gastric_tube"}:
            if kind in support:
                continue
            support.add(kind)
        unique.append(action)
    actions = unique
    # "Un electrocardiograma con derivadas derechas" names one study, not two.
    if any(a.get("diagnostic") in _LEAD_STUDIES for a in actions):
        actions = [a for a in actions if a.get("diagnostic") != "ecg"]
    seen, kept = set(), []
    for action in actions:
        key = action.get("diagnostic") if action.get("type") == "diagnostic" else None
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        kept.append(action)
    return kept
