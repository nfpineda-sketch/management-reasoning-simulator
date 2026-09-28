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
from shared_order_language import ROUTE_BEFORE_THE_DRUG, _normalize, _route, _amount


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
    "dextrose": {"dextrose": r"dextrose|dextrosa|glucosa(?:\s+intravenosa)?|glucosado|d50|d10"},
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
        "metamizole": r"metamizole?|dipirona|dipyrone|novalgina",
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
# "de" is the preposition of "4 U de GR", never the verb: read as "dé", it turned
# "pruebas cruzadas por 4 U de GR" into a transfusion of four units (TD-26).
_TRANSFUSING = re.compile(r"\b(?:transfund\w*|transfus\w*|pas(?:ar|o|e|a)|administr\w*|d(?:ar|oy|ale)|give|"
                          r"start|inici\w*|instal\w*|infund\w*)\b")

# Blood products as they are ordered at the bedside (TD-26, faculty decision of
# 2026-09-28). The engine runs packed red cells and models no other product.
# "2 U de GR O negativo", "O-neg", "packed cells" and the massive transfusion
# protocol were quoted back as unreadable, or lost without a word beside another
# order, and the Trace showed the resident not transfusing (cycle 6 blind sets).
_RED_CELL_NAMES = (r"p?rbcs?|packed\s+(?:red\s+)?(?:blood\s+)?cells|red\s+(?:blood\s+)?cells|globulos\s+rojos|"
                   r"concentrad[oa]s?\s+(?:de\s+)?(?:hematies|eritrocitos)|concentrad[oa]s?\s+eritrocitari[oa]s?|"
                   r"hematies|eritrocitos|paquetes?\s+globular(?:es)?|ugr")
# "Blood" and "sangre" name red cells, and not in "blood pressure", "blood bank",
# "blood glucose", "blood cultures", "estimated blood loss" or "banco de sangre":
# "Insulin 4 units SC for blood glucose 300" ran four units of red cells, and
# "Transfuse 2 units FFP with blood pressure checks" asked how many (adversarial
# review of cycle 7).
_BLOOD_WORD = (r"blood(?!\s+(?:pressure|bank|glucose|sugar|cultures?|gas\w*|loss|count|tests?|work|draw|typ\w*|group\w*|"
               r"products?|warmer|smear|levels?|alcohol|ph|volume|flow|vessels?|clots?|stream|results?|in\b))|"
               r"(?<!banco de )(?<!perdida de )(?<!perdidas de )"
               r"sangre(?!\s+(?:en|oculta|total|completa|perdida|venosa|arterial|capilar))")
_RED_CELL_WORDS = _RED_CELL_NAMES + "|" + _BLOOD_WORD
# "GR" is how red cells are written on a Chilean chart; "gr" after a dose is a
# gram. Red cells after a count of units, with what qualifies blood, beside
# another product ("GR/PFC"), or opening a chart line with its count ("GR 2 U",
# "GR: 2 U", "GR x 2"). "Ceftriaxona 2 gr/24h" is two grams a day, never red cells
# (adversarial review of cycle 7).
_OTHER_PRODUCT_SHORT = r"pfc|ffp|plasma|plaquetas|platelets|crio\w*|cryo\w*"
_GR_AS_RED_CELLS = re.compile(
    r"\b(?:u|unidad(?:es)?|units?)\s*(?:de\s+|of\s+)?gre?\b"
    r"|\bgre?\s*/\s*(?:" + _OTHER_PRODUCT_SHORT + r")\b|\b(?:" + _OTHER_PRODUCT_SHORT + r")\s*/\s*gre?\b"
    r"|^gre?\s*(?::\s*)?(?:x\s*)?\d+\s*(?:u\b|unidad(?:es)?\b|units?\b|$)"
    r"|\bgre?\s+(?:(?:o|0)\s*(?:rh\s*)?-?\s*(?:neg\w*|pos\w*)|isogrupo|isorh|sin\s+cruzar|no\s+cruzad\w*|"
    r"sin\s+esperar|"
    r"cruzad\w*|irradiad\w*|leucorreducid\w*|filtrad\w*)")
# Emergency-release red cells named by what they are, not by the product: "2
# units O-neg", "2 U O negativo", "O positivo", "uncrossmatched", "emergency release".
_RED_CELL_QUALIFIER = re.compile(
    r"\b(?:o|0)\s*(?:rh\s*)?-?\s*(?:neg|negativ[oae]s?|negative|pos|positiv[oae]s?|positive)\b|"
    r"\b(?:o|0)\s+rh\s*\(\s*[-+]\s*\)|\buncross(?:ed|matched)\b|"
    # "1 unidad O- a pasar ya": the sign written for the group (post hoc, blind set of cycle 7).
    r"(?<=\s)(?:o|0)\s*(?:rh\s*)?-(?=\s|$|[,.;])|"
    r"\bemergency[- ]release\b|\btype[- ]specific\b|\bsin\s+cruzar\b|\bno\s+cruzad[oa]s?\b")
# "2 PRBC now" and "Hang 4 PRBC" count the units by the product's name.
_BLOOD_UNIT_COUNT = re.compile(
    r"(?<![\w.])(\d+)\s*(?:u|units?|unidad(?:es)?|ugr|bolsas?|bags?|concentrad[oa]s?|paquetes?|p?rbcs?)\b"
    r"|\b(una|un|uno|one|dos|two|tres|three|cuatro|four|cinco|five|seis|six)\s+"
    r"(?:u|units?|unidad(?:es)?|bolsas?|bags?|concentrad[oa]s?|paquetes?|p?rbcs?)\b")
_UNIT_WORDS = {"una": 1, "un": 1, "uno": 1, "one": 1, "dos": 2, "two": 2, "tres": 3, "three": 3, "cuatro": 4,
               "four": 4, "cinco": 5, "five": 5, "seis": 6, "six": 6}
# One ratio or one count for several blood products: "1:1", "1:1:1", "4 U de cada
# uno", "4 units each", "c/u". A time ("14:05") is not a ratio.
_SHARED_BLOOD_COUNT = re.compile(r"(?<![\d:.])[1-4]\s*:\s*[1-4](?:\s*:\s*[1-4])?(?![\d:])|"
                                 r"\b(?:each|apiece|c/u|cada\s+un[oa]|de\s+cada\s+(?:un[oa]|producto))\b")
# Whole blood is not red cells: "low-titer O whole blood" ran as packed cells.
_WHOLE_BLOOD = r"whole\s+blood|ltowb|sangre\s+(?:total|completa)"
# The products the engine does not model. Each is recorded as ordered, with its
# physiologic effect not modelled, and never becomes red cells (TD-26, B). The
# names that can only be a product stand alone; "plasma" and "platelets" are
# also laboratory words, and are a product only when given or counted.
_PRODUCT_NAMES = (r"ffp|pfc|fresh\s+frozen\s+plasma|plasma\s+fresco(?:\s+congelado)?|thawed\s+plasma|"
                  r"cryo(?:precipitate)?s?|crioprecipitados?|" + _WHOLE_BLOOD +
                  r"|aferesis\s+de\s+plaquetas|pool\s+de\s+plaquetas|platelet\s+(?:pool|apheresis|transfusion)")
_PRODUCT_WORDS = r"plasma|platelets?|plaquetas|crio"
_GIVING_A_PRODUCT = re.compile(r"\b(?:transfund\w*|transfus\w*|give|giving|administ\w*|infund\w*|infuse|"
                               r"start|pas(?:ar|o|e|a|en)|d(?:ar|oy|ale)|inici\w*|hang|run)\b")
# Units asked to be ready, reserved or on their way are not a transfusion now:
# whether to give them or keep them reserved is the resident's to say (TD-26).
_RESERVING = re.compile(r"\b(?:reserv\w*|disponibles?|available|ready|listas?|listos?|standby|on\s+hold|hold|"
                        r"prepar(?:ar|o|e|a|en|ad[oa]s?)|prepare|preparing|a\s+disposicion|en\s+espera|"
                        r"on\s+the\s+way|en\s+camino|coming|cruz(?:ar|a|o|en|amos|ad[oa]s?)|crossmatched|"
                        r"typed\s+and\s+crossed)\b")
# "No cruzados", "sin cruzar" and "uncrossmatched" say the units are given now,
# without waiting for the crossmatch: the opposite of a reservation. Read as one,
# "pasar 2 UGR O negativo no cruzados ya" was asked whether to reserve them (A–J
# of cycle 7, independent set).
_NOT_WAITING_FOR_THE_CROSSMATCH = re.compile(
    r"\b(?:no\s+cruzad[oa]s?|sin\s+cruzar|uncross(?:ed|matched)|"
    r"(?:sin|no)\s+esperar\s+(?:(?:el|la|las|los|a)\s+)?(?:pruebas?\s+cruzadas?|pruebas?\s+de\s+compatibilidad|"
    r"cruzar|grupo_y_pruebas(?:\s+cruzadas)?|grupo|banco)|"
    r"(?:without|not)\s+waiting\s+(?:on|for)\s+(?:the\s+)?(?:type_and_screen|type\s+and\s+cross|crossmatch\w*|"
    r"cross\w*))")
# Units fetched are asked about as units asked for are ("pido 2 unidades de
# globulos rojos", 2026-09-24): "traigan 2 U de GR O negativo", "que suban 2 U"
# and "bring 2 units O-neg" ran as a transfusion once the chart-line reading
# read them.
_FETCHING = re.compile(r"^(?:que\s+)?(?:bring|fetch|get|send(?:\s+up)?|traig\w*|trae(?:r|n)?|sub(?:an|ir|e)|"
                       r"consig(?:an|a)|conseguir)\b")


def _held_back(text, verb=None):
    """Whether red cells are asked to be ready, crossmatched or fetched, rather than given now (TD-26)."""
    text = _NOT_WAITING_FOR_THE_CROSSMATCH.sub(" ", str(text or "")).strip()
    if re.search(r"\btransf(?:und|us)\w*", text) or verb in {"transfuse", "transfundir", "transfundo"}:
        return False
    if verb in {"aumentar"} or _FETCHING.match(text):
        return True
    crossmatched = re.search(r"\b(?:cruz(?:ar|a|o|en|amos|ad[oa]s?)|crossmatched|typed\s+and\s+crossed)\b", text)
    keeping = _RESERVING.search(re.sub(r"\b(?:cruz(?:ar|a|o|en|amos|ad[oa]s?)|crossmatched|typed\s+and\s+crossed)\b",
                                       " ", text))
    if keeping:
        return True
    # "Give 2 units of crossmatched PRBC": the crossmatch describes the units a
    # giving verb gives; without one, "2 U GR cruzadas" asks for the crossmatch.
    return bool(crossmatched) and not (_TRANSFUSING.search(text) or _TRANSFUSING.search(str(verb or "")))
_PRODUCT_COUNT = re.compile(r"(?<![\w.])\d+\s*(?:u|units?|unidad(?:es)?|bolsas?|bags?|pools?|aferesis|apheresis|"
                            r"doses?|dosis|ml/kg)\b|\b(?:una|one|dos|two|tres|three|cuatro|four|diez|ten)\s+"
                            r"(?:u|units?|unidad(?:es)?|bolsas?|bags?|pools?|aferesis|apheresis|doses?|dosis)\b")
# The massive transfusion protocol: its activation is recorded, and gives no
# product by itself (TD-26, C; charter §114). "Activo" opens it as often as a
# verb does, and is not a verb anywhere else here.
_MASSIVE_TRANSFUSION_NAMES = (r"massive\s+transfusion(?:\s+protocol)?|(?:protocolo\s+de\s+)?transfusion\s+masiva|"
                              r"major\s+ha?emorrhage\s+protocol|protocolo\s+de\s+hemorragia\s+masiva|mtp|ptm")
_MASSIVE_TRANSFUSION = re.compile(r"\b(?:" + _MASSIVE_TRANSFUSION_NAMES + r")\b")
# The protocol stood down (TD-32, cycle 8).
_MTP_STOP = re.compile(
    r"\b(?:deactivat\w*|desactiv\w*|stand(?:ing)?\s+down|stop|suspend\w*|cancel\w*|terminat\w*|end|finaliz\w*|"
    r"termin(?:ar|o|a|e|amos|en)|apag\w*)\s+(?:(?:the|el|la|al)\s+)?(?:" + _MASSIVE_TRANSFUSION_NAMES + r")\b"
    r"|\b(?:" + _MASSIVE_TRANSFUSION_NAMES + r")\s+(?:off|stood\s+down|deactivated|desactivad\w*|suspendid\w*|"
    r"cancelad\w*|terminad\w*|finalizad\w*)\b")
# The stand-down asked, suggested or written as the time of something else is not one (post hoc,
# adversarial review of cycle 8): "Stop MTP?", "Can we stop MTP now?", "We should stop MTP soon",
# "Once we stop MTP, recheck labs", "Cuando termine el PTM, controlar calcio iónico".
_MTP_STOP_NOT_NOW = re.compile(
    r"\?|\b(?:can|could|should|shall|may)\s+we\b|\bwe\s+(?:should|could|may|might|can)\b|\bsoon\b|\bpronto\b|"
    r"\b(?:podemos|podriamos|deberiamos|debemos|habria\s+que)\b|"
    r"\b(?:once|when|whenever|after|until|before|cuando|una\s+vez\s+que|tras|despues\s+de|hasta\s+que|antes\s+de|"
    r"en\s+cuanto)\s+(?:(?:we|the|el|la|se|lo|la)\s+)*(?:stop|stand|deactivat|desactiv|termin|suspend|finaliz|"
    r"cancel|end|apag)")
_ACTIVATING = re.compile(r"\b(?:activate|activating|activation|activaci[oó]n|call|trigger|initiate|start|declare|"
                         r"order|request|"
                         r"activ(?:ar|o|a|e|amos|emos|en|an)|llam(?:ar|o|a|e|amos|emos|en|an)|"
                         r"inici(?:ar|o|a|e|amos|emos|en|an)|solicit(?:ar|o|a|e|amos|emos|en|an)|"
                         r"pid(?:o|e|an|amos)|pedir|pedimos|gatill\w*|dispar(?:ar|o|a|e|amos|emos|en|an))\b")
# A count written on its own after the product it counts (A–J of cycle 7).
_A_COUNT_ALONE = re.compile(
    r"(?:(?:unas|unos|about|around|some|aprox\.?|aproximadamente)\s+)?"
    r"(?:\d+|una|un|uno|one|dos|two|tres|three|cuatro|four|cinco|five|seis|six|diez|ten)\s*"
    r"(?:u|units?|unidad(?:es)?|bolsas?|bags?|pools?|dosis|doses)"
    r"(?:\s+(?:del|de|of|from)\s+(?:(?:the|el|la)\s+)?(?:pool|banco|bank|aferesis|apheresis))?"
    r"(?:\s+(?:ahora|ya|now|stat|more|mas))?\s*[.!]?")
# Where a bleeding measure goes, written after it (A–J of cycle 7).
_WHERE_THE_MEASURE_GOES = re.compile(
    r"(?:(?:right|just|justo|bien|lo\s+mas|as|very|muy)\s+)*"
    r"(?:above|below|proximal|distal|over|on\s+top|arriba|encima|debajo|sobre|por\s+(?:encima|arriba|debajo)|"
    r"tight|apretad[oa]|high|high_and_tight|alt[oa]|deep|deeply|profund[oa]|firm(?:ly)?|firme)"
    r"(?:\s+(?:de|del|of|the|la|el|to|a|al|that|this|ese|esa|his|her|as|possible|posible))*"
    r"(?:\s+(?:wound|herida|knee|rodilla|elbow|codo|injury|lesion|bleed\w*|sangrado|site|sitio|laceration|"
    r"laceracion|thigh|muslo|arm|brazo|leg|pierna|groin|ingle|axilla|axila))?"
    r"(?:\s+(?:posible|possible|now|ya|ahora))?\s*[.!]?"
    # The tourniquet's time, written down with it: "note the time", "anotar hora".
    r"|(?:note|mark|record|write\s+down|anotar|anote|anoten|registrar|registre|marcar|marque)\s+"
    r"(?:the\s+|la\s+)?(?:time|hora)(?:\s+(?:de\s+)?(?:colocacion|placement|on))?\s*[.!]?")
# The protocol's cooler is how its activation is followed at the bedside: "get
# the cooler up here", "que suba la nevera" (A–J of cycle 7, independent set).
_BLOOD_COOLER = re.compile(r"(?:\b(?:get|bring|send|traigan|traer|trae|traiga|suba|suban|subir|pidan|pedir|pide|call\s+for)\s+"
                           r"(?:(?:the|la|el|una?|mtp|ptm)\s+)?(?:cooler|nevera|hielera|conservadora)\b"
                           r"|^(?:the\s+|la\s+|el\s+)?(?:cooler|nevera|hielera)\s+(?:up|here|now|ya|aqui|al\s+box))")
# A red-cell order spoken with the verb of the bag: "hang packed cells now" and
# "hang a unit of PRBC" were lost without a word beside another order (A–J).
# "De" is a preposition here, never the verb.
_GIVING_BLOOD = re.compile(r"\b(?:hang|hung|run|push|squeeze|pump|give|start|transfus\w*|transfund\w*|cuelg\w*|"
                           r"colg\w*|pong\w*|pon(?:er|go|ga)|instal\w*|coloqu\w*|coloc\w*|pas(?:ar|en|e|a)|"
                           r"administr\w*|d(?:ar|en|ale|enle)|infund\w*|inici\w*)\b")
# What may follow the protocol's name in its activation: "now", the products
# and units it is activated with, or a ratio. Anything else is a sentence about
# it ("MTP is likely", "transfusión masiva probable"), which is reasoning.
_AFTER_THE_PROTOCOL = re.compile(r"(?:now|ahora|ya|stat|immediately|inmediatamente|activad[oa]|activated|activation|"
                                 r"(?:with|con|and|y|plus|mas|\+)\b|\(?\d+\s*:\s*\d+)")
_GENERIC_BLOOD_PRODUCTS = re.compile(r"\b(?:blood\s+products?|hemoderivados?|productos?\s+sangu[ií]neos?|"
                                     r"componentes?\s+sangu[ií]neos?)\b")

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
    # Recorded as asked for, and modelled in no case (TD-22, cycle 7): no result
    # is invented. Unread, it held every other order of the submission, the CT
    # pulmonary angiogram of a young woman too.
    "pregnancy_test": r"(?:(?:urine|serum|quantitative|qualitative)\s+)?pregnancy\s+test|upt|"
                      r"(?:prueba|test|examen)\s+de\s+embarazo(?:\s+(?:en\s+orina|en\s+sangre|urinari[oa]|seric[oa]|"
                      r"cualitativ[oa]|cuantitativ[oa]))?|test\s*pack|"
                      r"(?:(?:serum|urine|quantitative|qualitative)\s+)?(?:beta[- ]?|b[- ]?|\u03b2[- ]?)?hcg"
                      r"(?:\s+(?:cuantitativa|cualitativa|en\s+orina|en\s+sangre|serica|urinaria|"
                      r"quantitative|qualitative))?|"
                      r"subunidad\s+beta(?:\s+(?:de\s+)?(?:la\s+)?hcg)?",
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
    "poc_glucose": r"poc glucose|blood glucose|blood sugar|fingerstick|finger stick|"
                   r"(?:glucosa|glicemia|glucemia)\s+capilar|glucose|glucosa|glicemia|glucemia|hgt|hemoglucotest",
    "chest_xray": r"chest x[- ]?ray|chest radiograph|cxr|radiografia(?:\s+(?:de\s+)?torax)?|"
                  r"rx(?:\s+de)?(?:\s+torax)?|placa(?:\s+(?:de\s+)?torax)?|x[- ]?rays?|radiograph",
    "urinalysis": r"urinalysis|urine analysis|urine dip|orina completa|examen de orina",
    "blood_cultures": r"blood cultures?|hemocultivos?",
    # Asked for beside the blood cultures, and read by the cultures of cycle 8, "urocultivo" was then
    # quoted back as unreadable and held the antibiotic written with it (post hoc, adversarial
    # review of cycle 8). Recorded as requested, with no result, as the pregnancy test is.
    "urine_culture": r"urine\s+cultures?|urocultivos?|cultivo\s+de\s+orina",
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
                        r"\b(?:peripheral\s+)?(?:iv|intravenous)\s+(?:line|access|cannula)\b|\blarge[- ]bore\b|"
                        # "Place a peripheral IV", "place a PIV", "start an IV": how the
                        # line is written in English (the twenty scenarios in English,
                        # 2026-09-25). "An IV bolus" or "an IV push" is a route, not a line.
                        r"\bpivs?\b|\bperipheral\s+ivs?\b|"
                        r"\b(?:an?|one|two|2)\s+ivs?\b(?!\s+(?:bolus|push|fluids?|infusion|drip|antibiotics?|dose))"),
    ("urinary_catheter", r"\bsonda\s+(?:foley|vesical|urinaria)\b|\bfoley\b|"
                         r"\burinary\s+catheter\b|\bindwelling\s+catheter\b"),
    ("gastric_tube", r"\bsonda\s+(?:nasogastrica|naso\s*gastrica|orogastrica)\b|\bsng\b|"
                     r"\bnasogastric\s+tube\b|\bng\s+tube\b"),
    ("npo", r"\bregimen\s+(?:cero|0)\b|\bnada\s+por\s+boca\b|\bayuno\b|\bnpo\b|\bnil\s+by\s+mouth\b"),
    # "Lo dejo en observacion 2 horas" keeps the patient under watch: until
    # 2026-09-24 it was dropped in silence, or held the whole order when a
    # glucose check followed it (rehearsal of the twenty-scenario batch).
    ("monitoring", r"\bmonitor(?:izacion|izar|izado|eo)?\b|\boximetr[ií]a\b|\bpulse\s+ox(?:imetry)?\b|"
                   r"\bunder\s+observation\b|"
                   r"\bcontinuous\s+monitoring\b|\bcardiac\s+monitor\b"),
)


_NAMES_A_DRUG = None

# A new peripheral line asked for without a verb (2026-09-26): a count or
# "nueva" before it, or "VVP" standing alone, which is how a chart writes it.
_VERBLESS_LINE = re.compile(
    r"\s*(?:(?:(?:nuevas?|otras?|\d+|una|dos)\s+)(?:vias?\s+venosas?(?:\s+perifericas?)?|vias?\s+perifericas?|vvps?)"
    r"|vvps?"
    r"|vias?\s+venosas?(?:\s+perifericas?)?\s+nuevas?"
    # The same line in English, named by its count or its bore: "2 large-bore IVs (16G)",
    # "two 18G IVs", "large-bore IV access x2" (TD-30, cycle 8). A bare "IV" is left alone:
    # after a dose it is the route.
    r"|(?:(?:\d+|one|two|a|an)\s*x?\s+)?(?:(?:(?:large|wide)[- ]?bore|big|peripheral|(?:14|16|18|20)\s*-?\s*g(?:auge)?)"
    r"\s+)+(?:ivs?|iv\s+lines?|iv\s+access|cannulas?|cannulae|lines?)"
    r"|(?:\d+|two|2x)\s+(?:ivs|iv\s+lines))"
    r"(?:\s+(?:nuevas?|gruesas?|de\s+grueso\s+calibre|bilaterales?|perifericas?|bilateral(?:ly)?|x\s*\d|now|stat|"
    r"(?:in|en)\s+(?:both|ambos)\s+(?:arms|antecubitals|brazos)|\((?:14|16|18|20)\s*-?\s*g(?:auge)?\)|"
    r"(?:14|16|18|20)\s*-?\s*g(?:auge)?))*"
    r"(?:\s+(?:or|o)\s+(?:an?\s+|una\s+)?(?:io|intraosseous|intraosea|via\s+intraosea))?\s*\.?\s*")


# A monitor asked for by its name, alone or as one item of a set-up list:
# "Monitor, vía venosa y oxígeno por mascarilla a 8 L/min", "monitor cardíaco",
# "cardiac monitoring". The bare word was read as the verb "monitor" with
# nothing to watch: it ordered nothing, "monitor cardíaco" came back as an
# order not recognized, and the verb passed on to the next items (DF-16a,
# 2026-09-28).
_MONITOR_ORDER = re.compile(
    r"(?:(?:cardiac|continuous|cardiorespiratory)\s+)?"
    r"monitor(?:ing|izacion|izar|izo|izamos|eo|ear|eamos|ea)?"
    r"(?:\s+(?:cardiac[oa]|continu[oa]|cardiorrespiratori[oa]|multiparametric[oa]|no\s+invasiv[oa]|"
    r"de\s+signos\s+vitales|ecg|ekg))?"
    r"|continuous\s+(?:cardiac\s+)?monitoring|cardiac\s+monitor(?:ing)?")
# A set-up item written the way a chart lists it, with no verb, as one item of a
# list: "Monitor, vía venosa y oxígeno…", "IV access, CBC and lactate", "vía
# venosa y régimen cero". In a list it asks for the support; it was dropped in
# silence (DF-16a, 2026-09-28). Alone, "vía venosa" is still not an order
# (test_hypoglycemia_reader, 2026-09-26), and words that describe what the
# patient already has keep it a description: "vía venosa permeable" is the line
# that came in with the patient.
_VERBLESS_SUPPORT_START = re.compile(
    r"(?:(?:\d+|una|un|dos|one|two|a|an)\s+)?"
    r"(?:vias?\s+(?:venosas?|perifericas?)|vvps?|accesos?\s+(?:venosos?|vasculares?)|cateter(?:es)?\s+venosos?|"
    r"(?:peripheral\s+)?(?:iv|intravenous)\s+(?:access|line|lines|cannula)|large[- ]bore\s+ivs?|pivs?|"
    r"regimen\s+(?:cero|0)|nada\s+por\s+boca|npo|nil\s+by\s+mouth|"
    r"sonda\s+(?:foley|vesical|urinaria|nasogastrica|orogastrica)|foley|sng|ng\s+tube|nasogastric\s+tube|"
    r"urinary\s+catheter)\b")
_DESCRIBES_SUPPORT = re.compile(
    r"\b(?:permeables?|patent|in\s+place|existing|funcionando|funcional(?:es)?|functioning|working|"
    r"instalad[oa]s?|puest[oa]s?|previas?|que\s+(?:trae|tiene)|ya\s+(?:tiene|trae)|already|"
    r"sin\s+cambios|retirad[oa]s?|removed|fallid[oa]s?|failed|infiltrad[oa]s?)\b")


def _verbless_support(body):
    """A set-up order listed without a verb, or None when it describes one."""
    if _DESCRIBES_SUPPORT.search(body):
        return None
    # "IV" alone is the line in the old "IV, O2, monitor"; after a dose it is a route.
    if re.fullmatch(r"(?:(?:\d+|una|dos|one|two)\s+)?ivs?", body):
        return {"type": "vascular_access", "operation": "start"}
    if not _VERBLESS_SUPPORT_START.match(body) or _names_a_drug(body):
        return None
    for kind, pattern in _SUPPORT_ORDERS:
        if re.search(pattern, body):
            return {"type": kind, "operation": "start"}
    return None


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


def _names_a_drug(body):
    return any(re.search(r"\b(?:" + pattern + r")\b", body) for agents in _AGENTS.values()
               for pattern in agents.values())


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
    r"volumen\s+corriente|respiratory\s+rate|set\s+rate|rate|frecuencia|fr\b|rr\b|flow|flujo|i\s*:\s*e|mode|modo|vc/ac|pc/ac|ac/vc|psv|"
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
    # "I place a chest tube", "we start norepinephrine": the first person is how
    # the order is spoken, and the pronoun is not the verb (DF-22, C07).
    r"^(?:(?:i\s+(?:will|want to)|i'll|i am going to|voy a|quiero|vamos a|i|we)\s+)?"
    r"(?P<verb>monitor|assess|vigilar|monitorizar|repeat|repetir|repito|repite|cardiovert|cardiovertir|cardiovierto|give|want|administer|apply|start|initiate|infuse|bolus|order|request|obtain|check|measure|send|get|perform|do|"
    r"stop|discontinue|disconnect|decompress|increase|decrease|lower|raise|titrate|continue|change|set|switch|adjust|modify|reduce|wean|transfuse|nebulize|place|insert|put|"
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
# The same orders said to the team, in the plural: "pasen", "pongan", "tomen",
# "hagan un test pack". Unread, such an order was lost without a word, and after
# a finding the negation took it (A–J of cycle 7, independent set). "Suban",
# "bajen", "manden", "envíen" and "dejen" are left out: each also fetches, sends
# or leaves, and red cells fetched are asked about.
_ES_TEAM_IMPERATIVES = {
    "iniciar": "inicien comiencen empiecen conecten", "administrar": "administren pasen carguen",
    "dar": "den", "poner": "pongan", "colocar": "coloquen instalen", "aplicar": "apliquen",
    "infundir": "infundan", "indicar": "indiquen", "pedir": "pidan", "solicitar": "soliciten",
    "medir": "midan", "controlar": "controlen", "obtener": "obtengan tomen", "realizar": "realicen",
    "hacer": "hagan", "suspender": "suspendan", "detener": "detengan", "retirar": "retiren",
    "sacar": "saquen", "aumentar": "aumenten", "disminuir": "disminuyan", "titular": "titulen",
    "continuar": "continuen", "mantener": "mantengan", "ajustar": "ajusten", "cambiar": "cambien",
    "transfundir": "transfundan", "nebulizar": "nebulicen", "consultar": "consulten",
    "interconsultar": "interconsulten", "llamar": "llamen avisen", "activar": "activen",
    "monitorizar": "monitoricen monitoreen", "hospitalizar": "hospitalicen", "ingresar": "ingresen",
    "induce": "induzcan", "sedate": "seden", "trasladar": "trasladen deriven", "intubar": "intuben",
    "ventilar": "ventilen", "reevaluar": "reevaluen",
}
for _verb, _forms in _ES_TEAM_IMPERATIVES.items():
    _ES_IMPERATIVES[_verb] += " " + _forms
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
# The fluids whose names end like an infinitive.
_SOLUTION_WORD = re.compile(r"ringers?|ringer\w*")


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
# intention starts its own clause. Exported: the reasoning capture parts a
# working model from the order after it at the same place (DF-7, 2026-09-27).
_DECLARED_INTENTION = re.compile(
    r"(?<=[^.;,\n])\s+(?=(?:i\s+(?:will|am\s+going\s+to)|i'll|i'm\s+going\s+to|"
    r"(?:le\s+|les\s+)?voy\s+a|vamos\s+a)\s+\w)", re.I)
# "For the massive hemothorax I place a left chest tube": an order in the first
# person present, after the reason for it (DF-22, C07, 2026-09-28). Not in a
# question ("Should I give aspirin 300 mg PO?"), a hedge or a habit ("I think we
# start…", "normally we start… but not now"), a condition ("when MAP < 65 we
# start…") or a clause that reports ("that we give too much fluid"): those ran
# as orders, and the last cut the working model short (adversarial review of
# cycle 6).
_FIRST_PERSON_ORDER = re.compile(
    r"(?<=[^.;,\n])\s+(?=(?:i|we)\s+(?:start|give|place|insert|put|order|request|call|consult|activate|administer|"
    r"begin|intubate|transfuse|apply|perform|obtain|send|stop|discontinue|hold|increase|decrease|titrate|"
    r"reassess|draw)\b)", re.I)
_NOT_A_FIRST_PERSON_ORDER = re.compile(
    r"\b(?:should|shall|can|could|would|do|does|did|may|might|must|why|what|how|whether|if|unless|when|"
    r"whenever|once|after|before|until|in\s+case|that|think|believe|guess|suppose|wonder\w*|consider\w*|"
    r"normally|usually|generally|typically|often|sometimes|always|never|routinely|habitually)\b", re.I)


def _first_person_split(match):
    text = match.string
    start = max(text.rfind(mark, 0, match.start()) for mark in ".;\n") + 1
    ends = [index for index in (text.find(mark, match.end()) for mark in ".;\n") if index >= 0]
    end = min(ends) if ends else len(text)
    if "?" in text[start:end] or _NOT_A_FIRST_PERSON_ORDER.search(text[start:match.start()]):
        return match[0]
    return ", "


# In Spanish the intention is a periphrasis around the infinitive the parser
# already knows: "le voy a pasar volumen" is "pasar volumen" announced. Removing
# the periphrasis puts the infinitive where a clause-initial order belongs.
_ES_INTENTION = re.compile(
    r"(^|[.;,\n]\s*)(?:(?:me|te|se|nos|le|les|lo|la|los|las)\s+)?"
    r"(?:voy\s+a|vamos\s+a)\s+(?=\w)", re.I)


# "Ahora salbutamol 5 mg nbz y luego repetir…", "Now give epinephrine…",
# "Primero E-FAST": a word of time that opens a clause is not the order, and
# with it in front neither the verb nor the drug started the clause, so the
# order was read as nothing -- and a repeat after it was kept as a plan of
# nothing (DF-22, C03 and H02, 2026-09-28). "Ya" is not one of them: "ya pase
# 1 litro" says what was already given.
_OPENING_TIME_WORD = re.compile(
    r"(^|[.;:\n]\s*|,\s*|\b(?:y|e|and|then|luego)\s+)"
    r"(?:ahora(?:\s+mismo)?|now|right\s+now|primero|first(?:ly)?|inmediatamente|immediately|"
    # "Y de una vez pasen 2 GR", "al tiro": how "now" is said in Chile (A–J of cycle 7).
    r"de\s+inmediato|de\s+una\s+vez|al\s+tiro|altiro|ya\s+mismo|stat|urgente(?:mente)?|urgently)\s*,?\s+(?=\w)")


# A running crystalloid is stopped in more ways than "stop" and "suspender":
# "hold the saline", "D/C the fluids", "cierra el SF", "corta el suero". Read as
# a withholding or as nothing, the stop was lost while the new fluid started,
# and both ran (DF-22, C04; found by the blind held-out check, 2026-09-28). Only
# before a fluid the reader knows: "para el dolor" is still "for the pain".
_FLUID_STOP_VERB = re.compile(
    r"\b(?:hold|d/c|dc|turn\s+off|shut\s+off|cierra|cierre|cerrar|corta|corte|cortar|apaga|apague|apagar|"
    r"para|parar|pare|detener|deten|detenga)\s+(?=(?:(?:the|el|la|los|las|su|sus)\s+)?"
    r"(?:saline|normal\s+saline|ns|sf|suero(?:\s+fisiologico)?|sueros|ringer\w*|lactated\s+ringer\w*|lr|rl|"
    r"hartmann|fluids?|fluidos?|crystalloids?|cristaloides?|maintenance\s+fluids?)\b"
    # The fluid ends the clause: "para los fluidos: Ringer 500 mL" and "para el
    # SF: 500 mL en bolo" are "for", and stopped the fluid they ordered (found by
    # the adversarial review of cycle 6, 2026-09-28).
    r"(?:\s+(?:now|ahora|ya|stat|immediately|inmediatamente))?\s*(?:$|[.;,\n]|(?:y|e|and|then|luego)\b))")


def _fluid_stop_verbs(text):
    return _FLUID_STOP_VERB.sub("stop ", text)


# The line an order runs through is its route, not a second order: "SF 500 mL
# por VVP en 15 min", "pasar 1 L de Ringer por via venosa periferica", "give
# 500 mL NS via the PIV" placed a peripheral line and lost the bolus without a
# word (found by the blind held-out check of DF-22, where C01 had started to run
# the order written before a condition, 2026-09-28). Only after something else:
# "VVP", "2 VVP" and "instalar VVP" still ask for the line.
_THROUGH_THE_LINE = re.compile(
    r"(?<=\S)\s+(?P<by>por|a\s+traves\s+de|through|via|by)\s+"
    r"(?:(?:la|el|una|un|su|the|a|an|his|her|their)\s+)?"
    r"(?:vvps?|vias?\s+venosas?(?:\s+perifericas?)?|vias?\s+perifericas?|branula|acceso\s+venoso(?:\s+periferico)?|"
    r"pivs?|peripheral\s+ivs?|peripheral\s+lines?|(?:large[- ]bore\s+)?iv(?:\s+(?:line|access))?)\b")


def _through_the_line(text):
    return _THROUGH_THE_LINE.sub(
        lambda match: " ev" if match["by"] in ("por", "a traves de") or match["by"].startswith("a ") else " iv", text)


def _opening_time_word(text):
    return _OPENING_TIME_WORD.sub(r"\1", text)


def _declared_intention(text):
    text = _FIRST_PERSON_ORDER.sub(_first_person_split, _DECLARED_INTENTION.sub(", ", str(text or "")))
    return _ES_INTENTION.sub(r"\1", text)


# "Por el hemotorax masivo izquierdo instalo tubo pleural izquierdo", "ante la
# hipotension inicio noradrenalina": the reason first and then the order, in the
# first person, with no comma between them. The order verb opens a clause only at
# the start of a sentence, so the tube was never placed and the page ran only
# the reassessment written after it (DF-22, C07, 2026-09-28). Stripped of its
# accent, "inicio" is also "inicio" (he started), so this is read only in a
# sentence that opens with its reason, never across a comma, and never when the
# reason names someone else who could be the one acting ("el paramedico inicio").
_ES_FIRST_PERSON_ORDER = (r"instalo|inicio|coloco|administro|pongo|doy|indico|solicito|pido|suspendo|paso|"
                          r"aplico|transfundo|nebulizo|consulto|interconsulto|llamo|aviso|hospitalizo|derivo|"
                          r"intubo|ventilo|activo|titulo|ajusto|agrego|repito|reevaluo|mido|cardiovierto")
_ES_REASON_FIRST = re.compile(
    r"(^|[.;\n][^\S\n]*)((?:por|ante|dado|dada|debido\s+a|como|frente\s+a|en\s+vista\s+de|considerando)"
    r"(?:[^\S\n]+[^\s.;,:]+){1,9}?)"
    r"[^\S\n]+(?=(?:(?:le|les|lo|la|los|las)\s+)?(?:" + _ES_FIRST_PERSON_ORDER + r")\b)")
# "Por qué no inicio noradrenalina?", "por lo general administro aspirina": a
# question and a habit are not the reason for an order now; both ran as orders
# (adversarial review of cycle 6). The reason above is read word by word: with
# "[^.;,:]*?" a run of spaces made the pattern cubic and froze the page.
_NOT_A_REASON = re.compile(
    r"(?:por|como)\s+(?:que|lo\s+(?:general|comun|habitual|usual|normal)|costumbre|regla|norma|rutina|habito)\b")
# Someone else as the subject right before the verb: "por la disnea el
# paramedico inicio oxigeno" is history, not an order. "La hipotension del
# paciente" names the patient as a possessor, not as the one acting.
_SOMEONE_ELSE = re.compile(
    r"\b(?:el|la|los|las|su|sus|un|una|mi|nuestro|nuestra)\s+(?:\w+\s+)?"
    r"(?:paciente|medic[oa]s?|paramedic[oa]s?|samu|familia|esposa?|marido|madre|padre|hij[oa]s?|"
    r"enfermer[oa]s?|equipo|tratante|cardiolog[oa]s?|colega|residente|interno)"
    r"(?:\s+(?:le|les|lo|la|los|las))?$"
    r"|\b(?:el|ella|ellos|ellas|usted)(?:\s+(?:le|les|lo|la|los|las))?$")
_ARTICLE_BEFORE = re.compile(r"\b(?:el|la|los|las|un|una|del|al|de|su|sus|mi|este|esta)$")


# "Antes de seguir hagan un test pack rápido": the step named first, then the
# team's order, with no comma between them. The order verb opens a clause only at
# its start, so the pregnancy test was lost without a word beside the adrenaline
# (TD-22, A–J of cycle 7, independent set).
_BEFORE_THEN_TEAM_ORDER = re.compile(
    r"(^|[.;\n][^\S\n]*)(antes\s+de(?:[^\S\n]+[^\s.;,:]+){1,5}?)[^\S\n]+(?=(?:"
    + "|".join(sorted({form for forms in _ES_TEAM_IMPERATIVES.values() for form in forms.split()},
                      key=len, reverse=True)) + r")\b)")


def _correcting_with(text):
    """ "Corrijan con suero glucosado": correcting with a treatment is giving it.

    Unread, the glucose was lost beside the venous gases written after it (A–J of
    cycle 7, independent set).
    """
    return re.sub(r"\b(?:corrig\w*|corrij\w*)\s+con\b", "administrar", text)


def _reason_then_order(text):
    text = _BEFORE_THEN_TEAM_ORDER.sub(lambda match: match[1] + match[2] + ", ", text)

    def replace(match):
        reason = match[2]
        if _SOMEONE_ELSE.search(reason) or _ARTICLE_BEFORE.search(reason) or len(reason.split()) > 9:
            return match[0]
        ends = [index for index in (match.string.find(mark, match.end()) for mark in ".;\n") if index >= 0]
        clause = match.string[match.start():min(ends) if ends else len(match.string)]
        if _NOT_A_REASON.match(reason) or "?" in clause or "¿" in clause:
            return match[0]
        return match[1] + reason + ", "
    return _ES_REASON_FIRST.sub(replace, text)


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


# "Activo hemodinamia", "activamos el codigo infarto": the first person of
# "activar" is how the reperfusion pathway is called, and it is deliberately not
# in the imperative table ("sangrado activo"). Only before what can be activated
# is it the verb. Without it the call vanished and the page ran only the ECG
# written after it (DF-22, C06, 2026-09-28).
_ES_ACTIVATION = re.compile(
    r"\b(?:activo|activamos|active|activen)\s+(?=(?:(?:el|la|los|al|a)\s+)?"
    r"(?:hemodinamia|hemodinamica|pabellon|codigo|protocolo|equipo|cath|cardiolog))")


def _spanish_imperatives(text):
    """Read a clause-initial imperative as the infinitive the parser knows."""
    text = _ES_STOP_PERIPHRASIS.sub("suspender ", text)
    text = _ES_START_PERIPHRASIS.sub("administrar ", text)
    text = _ES_ACTIVATION.sub("activar ", text)
    def replace(match):
        if match[2] in _ES_NOUN_FORMS and _ES_NOUN_PHRASE.match(match.string[match.end():]):
            return match[0]
        following = _ES_PERIPHRASIS.match(match.string[match.end():])
        # "Cambia a ringer lactato 500 ml": "ringer" ends like an infinitive
        # and is a fluid. Read as "empieza a agotarse", the verb was left
        # unread, the clause inherited the "suspende" before it, and the
        # Ringer's the resident switched to was stopped instead of started
        # (DF-22, C04, 2026-09-28).
        if (following and following[1] not in _ES_IMPERATIVE_FORMS.values()
                and not _SOLUTION_WORD.fullmatch(following[1])):
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
    r"auto-?inyector|auto-?injector|epi-?pen)\b"
    r"|\b(?:indic\w*|recet\w*|prescrib\w*)\b.*\b(?:al|para\s+el)\s+alta\b"
    r"|\b(?:prescribe|prescribed)\b.*\b(?:at|on|for)\s+discharge\b")

# A glucose solution at a concentration the engine does not run as an infusion.
# It models a dextrose dose and the 10% infusion; "suero glucosado al 5% a 100
# ml/h" was read as the 10% infusion (hypoglycaemia reader checks, 2026-09-26).
# A concentration below 10%, or any other than 10% given at a rate, is recorded
# as the resident's indication with its effect not modelled (faculty decision 3),
# never converted. A bolus written as concentration and volume ("glucosa al 30%
# 50 mL") is still a dose (faculty decision 2).
_DEXTROSE_SOLUTION = re.compile(r"\b(?:suero\s+glucosado|solucion\s+glucosada|glucosado|sg|dextros[ae]|glucosa)\b"
                                r"|\bd\s*(?=\d)")
_SOLUTION_PERCENT_ANY = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_D_NUMBER = re.compile(r"\bd\s*(\d+(?:[.,]\d+)?)\s*w?\b")
_INFUSION_CONTEXT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:ml|cc)\s*(?:/|\s+(?:por|per|cada)\s+)\s*(?:h|hr|hora|hour)\b"
                               r"|\binfusi|\bgoteo\b|\bbic\b|\bmantenci|\bmaintenance\b")


def _unmodelled_dextrose(piece):
    """True for a glucose solution the engine would misread as its 10% infusion."""
    text = str(piece or "").lower()
    if not _DEXTROSE_SOLUTION.search(text):
        return False
    match = _SOLUTION_PERCENT_ANY.search(text) or _D_NUMBER.search(text)
    if not match:
        return False
    percent = float(match.group(1).replace(",", "."))
    if percent == 10:
        return False
    return percent < 10 or bool(_INFUSION_CONTEXT.search(text))


# The medicine an unmodelled indication names, and whether it is for home. The
# massive transfusion protocol and the blood products the engine does not run
# are read first: "plasma" is never "a medicine" (TD-26).
_UNMODELLED_CLASSES = (
    # A product ordered "per MTP" is the product; the activation is recorded on
    # its own (adversarial review of cycle 7).
    ("blood_product", _PRODUCT_NAMES + "|" + _PRODUCT_WORDS),
    ("massive_transfusion", _MASSIVE_TRANSFUSION_NAMES),
    # "Adrenalina autoinyectable" is the same prescription (post hoc, adversarial review of cycle 8).
    ("adrenaline_autoinjector", r"auto-?inyect(?:or|able)|auto-?inject(?:or|able)|epi-?pen"),
    ("antihistamine", r"clorfenamina|clorfeniramina|chlorphenamine|chlorpheniramine|difenhidramina|diphenhydramine|"
                      r"antihistaminic[oa]s?|antihistamines?|cetirizina|cetirizine|loratadina|loratadine|"
                      r"desloratadina|hidroxicina|hydroxyzine"),
    ("h2_blocker", r"famotidina|famotidine|ranitidina|ranitidine"),
    ("benzodiazepine", r"lorazepam|diazepam|alprazolam|clonazepam|benzodiacepinas?|benzodiazepines?"),
    ("antiemetic", r"ondansetron|metoclopramida|metoclopramide"),
)
_FOR_HOME = re.compile(r"\b(?:al|para\s+el)\s+alta\b|\b(?:at|on|for)\s+discharge\b|\bpara\s+la\s+casa\b")


def unmodelled_detail(text):
    """{category, agent, prescription} for a medicine the simulator does not model."""
    lowered = _normalize(str(text or ""))
    stop = _MTP_STOP.search(lowered)
    if stop:
        return {"category": "massive_transfusion_stop", "agent": stop.group(0), "prescription": False}
    category, agent = "other", ""
    for name, pattern in _UNMODELLED_CLASSES:
        match = re.search(r"\b(?:" + pattern + r")\b", lowered)
        if match:
            category, agent = name, match.group(0)
            break
    prescription = bool(_FOR_HOME.search(lowered)) or category == "adrenaline_autoinjector"
    return {"category": category, "agent": agent, "prescription": prescription}


# The bleeding measures, each as the resident names it. What the engine performs
# is one of three measures; a dressing is recorded by its own name and applied
# as the measure it is (C7-06). "Hemorrhage control" without a measure, or "stop
# the bleeding", names no measure, and the engine asks which one.
_HAEMORRHAGE_MEASURES = (
    ("tourniquet", None, r"torniquetes?|tourniquets?"),
    ("packing", None, r"empaquetamiento|empaquet(?:ar|o|a|e|amos|en)|packing|"
                      # "Empaquen la herida" is "empacar", as it is said in Chile (A–J).
                      r"(?:empac(?:ar|o|a|amos|an)|empaqu(?:e|en|emos))\s+(?:(?:bien\s+)?(?:la|el|esa|ese|esta|este)\s+)?"
                      r"(?:herida|sitio|lesion|zona|cavidad|laceracion)|"
                      r"(?:empac(?:ar|o|a|amos|an)|empaqu(?:e|en|emos))\s+con\s+gasa|"
                      r"pack(?:ed)?\s+(?:(?:the|this|that|his|her)\s+)?(?:wound|laceration|bleeding|site|groin|axilla|"
                      r"neck|defect|cavity|it)|"
                      # "Taponamiento" is packing only with the wound it packs, or as the
                      # thing done: "FAST para descartar taponamiento" packed a wound
                      # (adversarial review of cycle 7).
                      r"taponamiento\s+(?:de\s+(?:la\s+)?(?:herida|sitio|lesion|laceracion|zona)|con\s+gasas?|"
                      r"compresivo)|"
                      r"(?:hacer|haga|hagan|hago|realizar|realice|realicen|realizo)\s+(?:un\s+)?taponamiento"
                      r"(?!\s+(?:cardiaco|pericardico|cardiac|pericardial|con\s+balon))|"
                      r"tapon(?:ar|o|a|e|amos)\s+(?:(?:la|el)\s+)?(?:herida|sangrado|laceracion|sitio|zona)"),
    ("direct pressure", "pressure dressing", r"(?:vendaje|aposito)\s+compresivo|pressure\s+dressing"),
    ("direct pressure", "hemostatic dressing", r"(?:vendaje|aposito|gasa)\s+hemostatic[oa]|h[ae]mostatic\s+(?:dressing|gauze)"),
    ("direct pressure", None, r"(?:compresion|presion)\s+(?:directa|manual|externa|firme)|direct\s+pressure|"
                              r"(?:firm|manual|constant|steady)\s+pressure(?!\s+(?:support|control|ventilation|mode))|"
                              r"(?:hold|holding|apply|applying)\s+(?:(?:firm|direct|manual|constant|steady)\s+)?"
                              r"pressure(?!\s+(?:support|control|ventilation|mode|target|goal|above|below|over\s+\d|"
                              r"meds|medications?|medicines?|drugs?|agents?|pressors?|at\s+\d|of\s+\d|\d))|"
                              r"(?<!blood )(?<!arterial )pressure\s+(?:on|over|to)\s+(?:the\s+)?(?:wound|bleeding|site|"
                              r"laceration|groin|axilla|neck|leg|arm|thigh|scalp)(?!\s+(?:is\s+)?\d)|"
                              r"presion\s+(?:sobre|en)\s+(?:(?:la|el)\s+)?(?:herida|sangrado|sitio|punto|zona|lesion|"
                              r"laceracion)|"
                              r"(?:hacer|hago|haga|haz|ejercer|ejerzo|ejerza)\s+(?:una\s+)?presion|"
                              r"presion\s+(?:por|durante)\s+\d+\s*min\w*|pressure\s+for\s+\d+\s*min\w*|"
                              r"compri(?:mir|mo|ma|me|mimos)\s+(?:(?:la|el)\s+)?(?:herida|sangrado|sitio|punto|zona|"
                              r"lesion)|"
                              # Kept pressure, where it is kept: "mantengan presión encima", "keep
                              # pressure on it". Never alone: "para mantener presión" is the blood
                              # pressure (A–J of cycle 7).
                              r"manten(?:er|go|ga|gan|gamos)?\s+(?:la\s+)?presion(?:\s+(?:directa|firme|manual|"
                              r"constante))?\s+(?:encima|arriba|sobre\s+(?:(?:la|el)\s+)?(?:herida|gasa|sitio|zona|"
                              r"punto|lesion)|en\s+(?:(?:la|el)\s+)?(?:herida|sitio|zona|punto)|con\s+(?:la\s+)?(?:mano|"
                              r"gasa))|"
                              r"(?:keep|keeping|maintain|maintaining)\s+(?:(?:firm|direct|manual|constant|steady)\s+)?"
                              r"pressure\s+(?:on|over)\s+(?:it|top|the\s+(?:wound|bleed\w*|site|gauze|dressing|"
                              r"packing))"),
)
_UNNAMED_MEASURE = re.compile(
    r"\b(?:control\s+de\s+(?:la\s+)?hemorragia|control\s+del\s+sangrado|h[ae]morrhage\s+control|"
    r"bleeding\s+control)\b"
    # The same, said to the team: "somebody control that bleeding now", "que
    # alguien controle ese sangrado ya" were answered with nothing to go on (A–J).
    # Only with whoever is told to do it, or the bleeding pointed at: "control
    # the bleeding" is also the goal a reasoning line states ("they do the
    # endoscopy and control the bleeding"), and it held a consult.
    r"|(?:(?:somebody|someone|alguien|que\s+alguien)\s+(?:control|controle|controlen|controla|stop|detenga|detengan|"
    r"pare|paren)\s+(?:(?:that|the|this|his|her|ese|esa|el|la|este|esta)\s+)?|"
    r"(?:control|controlar|controle|controlen|controla|stop|detener|deten|detenga|detengan|parar|pare|paren)\s+"
    r"(?:that|this|ese|esa|este|esta)\s+)(?:bleed\w*|h[ae]morrhag\w*|sangrado|sangramiento|hemorragia)\b")


# An intraosseous line, by its site, by what it is or by placing it: "humeral IO",
# "IO access", "EZ-IO", "acceso intraóseo tibial", "coloco una vía intraósea",
# "place an IO". A bare "IO" or "vía IO" names a route: written after a dose it is
# that dose's route, and it is never read as a line placed (C7-06).
_IO_ACCESS = re.compile(
    r"\b(?:(?:humeral|tibial|sternal|femoral|proximal\s+(?:humeral|tibial)|distal\s+(?:femoral|tibial))\s+"
    r"(?:io|intraosseous)|"
    r"(?:io|intraosseous)\s+(?:access|line|needle|catheter|cannula|device|drill|"
    r"in\s+the\s+(?:(?:left|right|proximal|distal)\s+)*(?:humerus|tibia|sternum|femur)|"
    r"(?:(?:left|right|proximal|distal)\s+)*(?:humeral|tibial|sternal|femoral))|"
    r"ez[- ]?io|"
    r"(?:acceso|aguja|cateter|puncion|linea)\s+(?:intraose[ao]s?|io)|"
    r"(?:vias?\s+)?(?:intraose[ao]s?|io)\s+(?:humeral|tibial|esternal|femoral|"
    r"en\s+(?:(?:el|la)\s+)?(?:humero|tibia|esternon|femur))|"
    r"(?:place|placing|insert|inserting|drill|establish|get|obtain|start)\s+(?:an?\s+)?"
    r"(?:(?:humeral|tibial|left|right)\s+)*(?:io|intraosseous)|"
    r"(?:instal\w*|canaliz\w*|coloc\w*|pon(?:er|go|e|ga)|dej(?:ar|o)|obten\w*)\s+(?:(?:una?|la|el)\s+)?"
    r"(?:(?:via|linea|acceso)\s+)?(?:io|intraose[ao]s?))\b")
_IO_STATUS = re.compile(
    r"\b(?:is|are|was|were|esta|estan|fue|failed|fallo|fallid[oa]|infiltrad\w*|infiltrated|working|funciona\w*|"
    r"in\s+place|en\s+su\s+lugar|dislodged|desplazad\w*|salid[oa]|not\s+working|no\s+funciona|through\s+it|"
    r"por\s+ella|from\s+ems|del\s+samu)\b")
_BARE_IO = re.compile(r"(?:(?:una?|la|el|an?)\s+)?(?:(?:via|linea)\s+)?(?:io|intraosseous|intraose[ao])\s*[.!]?")
_PLACING_IO = re.compile(r"(?:(?:an?|una?|la|el)\s+)?(?:(?:via|linea)\s+)?(?:(?:humeral|tibial)\s+)?"
                         r"(?:io|intraosseous|intraose[ao])\b")


# A device removed, loosened or replaced is not applied: "Remove the tourniquet"
# and "Convert tourniquet to pressure dressing" applied it (adversarial review of
# cycle 7; partly as before). Removing it is not modelled, and is quoted back.
_REMOVING_A_MEASURE = re.compile(
    r"\b(?:remove|removing|take\s+off|loosen\w*|release|convert\w*|replace|replac\w*|retir\w*|quit\w*|sac(?:ar|a|o|en)|"
    r"afloj\w*|solt\w*|cambi\w*|reemplaz\w*|convertir|deflate|desinfl\w*)\b")


# A measure named by what it is, whatever is done with it.
_MEASURE_NAMED = re.compile(r"\b(?:torniquetes?|tourniquets?|packing|empaquetamiento|(?:vendaje|aposito)\s+"
                            r"(?:compresivo|hemostatico)|(?:pressure|hemostatic|haemostatic)\s+dressing|"
                            r"(?:direct|manual)\s+pressure|(?:presion|compresion)\s+(?:directa|manual))\b")
# What a stopping verb stops here: the bleeding, never a measure. "Detener
# sangrado: presión directa", "stop the bleeding with direct pressure" and "detén
# el sangrado con un torniquete" were quoted back once a stopping verb was read as
# the measure removed (post hoc, cycle 7).
_STOPPING_THE_BLEEDING = re.compile(
    r"\b(?:stop|detener|deten|detenga|detengan|detengo|suspender|parar|pare|paren|frenar|frena|frene|cohibir)\s+"
    r"(?:(?:the|that|this|his|her|el|la|ese|esa|este|esta)\s+)?"
    r"(?:bleed\w*|h[ae]morrhag\w*|sangrado|sangramiento|hemorragia)\b")


def _haemorrhage_measures(text, verb=None):
    """[(measure, name the resident used or None)] in the order written; [(None, None)] for no measure named."""
    text = str(text or "")
    if _REMOVING_A_MEASURE.search(text) or (
            verb in {"retirar", "retiro", "sacar", "saco", "stop", "discontinue", "suspender", "suspendo", "detener"}
            and not _STOPPING_THE_BLEEDING.search(text)
            # A measure with a verb of its own is not what a stop lent to the list
            # stops: "stop the bleeding and hold pressure" (post hoc, cycle 7).
            and not re.match(r"(?:hold|apply|pack|keep|maintain|compress|empaquet\w*|empac\w*|comprim\w*|"
                             r"hac(?:er|e)|haga|hagan|hago|ejerc\w*|ejerz\w*|manten\w*|tapon\w*)\b", text.strip())):
        return []
    found = []
    for measure, named, pattern in _HAEMORRHAGE_MEASURES:
        for match in re.finditer(r"\b(?:" + pattern + r")\b", text):
            if not any(start <= match.start() < end for _, _, start, end in found):
                # "Nurse is holding pressure", "was holding pressure": what is being
                # or was done, not an order (adversarial review of cycle 7).
                if re.search(r"\b(?:is|are|was|were|esta|estan|estaba|estaban|been|held|hice|hicimos|hizo|tried|"
                             r"intente|intentamos|applied|aplique|aplicamos)\s+$", text[:match.start()]):
                    continue
                found.append((measure, named, match.start(), match.end()))
    if any(measure == "packing" for measure, _, _, _ in found) and re.search(
            r"\b(?:preperitoneal|pelvic|pelvico|abdominal|surg\w*|cirug\w*|quirurg\w*|operating|theatre|theater|"
            r"pabellon|quirofano|damage\s+control)\b|\bin\s+(?:the\s+)?or\b", text):
        # Packing done by surgery in the operating room is not a bedside measure.
        found = [item for item in found if item[0] != "packing"]
    if len(found) > 1 and re.search(r"\b(?:or|o|u)\b", text):
        # "Tourniquet or direct pressure": an alternative, asked about (A–J).
        return [(None, None)]
    # "Empaquetar la herida y comprimir": a bare "compress" beside nothing else.
    if not found and re.fullmatch(r"\s*(?:comprimir|comprimo|comprima|comprime|compress|compression)\s*[.!]?", text):
        found.append(("direct pressure", None, 0, len(text)))
    # Only as the order itself: "endoscopía para control del sangrado" asks for
    # an endoscopy, and whoever stops the bleeding there is not a measure here.
    if not found and _UNNAMED_MEASURE.match(text.strip()) and not re.search(
            r"\b(?:endoscop\w*|gastro\w*|cirug\w*|surg\w*|angio\w*|emboliz\w*|interventional|radiolog\w*|"
            r"quirofano|pabellon|operating|theatre|theater)\b", text):
        return [(None, None)]
    if any(measure == "packing" for measure, _, _, _ in found):
        # "Packing con gasa hemostática": the gauze is what the wound is packed with.
        found = [item for item in found if item[1] != "hemostatic dressing"]
    ordered, seen = [], set()
    for measure, named, _, _ in sorted(found, key=lambda item: item[2]):
        if (measure, named) not in seen:
            seen.add((measure, named))
            ordered.append((measure, named))
    return ordered


def red_cells_named(body, verb=None):
    """Whether a clause names packed red cells, the one blood product the engine runs."""
    body = str(body or "")
    if re.search(r"\b(?:" + _WHOLE_BLOOD + r")\b", body) or _GENERIC_BLOOD_PRODUCTS.search(body):
        return False
    if re.search(r"\b(?:" + _RED_CELL_WORDS + r")\b", body) or _GR_AS_RED_CELLS.search(body):
        return True
    # "2 GR" or "3 GR ahora" on its own line names no medicine a gram could be of.
    if re.fullmatch(r"(?:\d+|una?|uno|dos|tres|cuatro)\s*gre?\b(?:\s+(?:ahora|ya|now|stat|urgente|(?:o|0)\s*"
                    r"(?:rh\s*)?-?\s*(?:neg\w*|pos\w*)))*\s*[.!]?", body.strip()):
        return True
    transfusing = verb in {"transfuse", "transfundir", "transfundo"} or bool(re.search(r"\btransf(?:und|us)\w*", body))
    if transfusing and re.search(r"\bgre?\b(?!\s*/)", body):
        return True
    # "Transfundo 1 más", "transfundir 2 ahora": a transfusion counted, and nothing else named.
    if transfusing and re.fullmatch(r"\d\s*(?:u\b|units?|unidad(?:es)?)?\s*(?:mas|more|adicional(?:es)?|extra|ahora|ya|"
                                    r"now|stat)?\s*[.!]?", body.strip()):
        return True
    # "Transfundir 1 U más": a transfusion counted in units, with no product named, is red cells.
    if transfusing and _BLOOD_UNIT_COUNT.search(body) and not re.search(
            r"\b(?:" + _PRODUCT_NAMES + "|" + _PRODUCT_WORDS + r")\b", body):
        return True
    return bool(_RED_CELL_QUALIFIER.search(body)) and (transfusing or bool(_BLOOD_UNIT_COUNT.search(body)))


def blood_units(body):
    """The number of units written, once, in figures or as a word; None when absent or ambiguous."""
    body = str(body or "")
    found = [float(match[1]) if match[1] else float(_UNIT_WORDS[match[2]])
             for match in _BLOOD_UNIT_COUNT.finditer(body)]
    if not found:
        # Read only once the clause is red cells: "transfundir 3 GR" is three
        # units, "hang a unit of PRBC" is one and "transfundir 2 ahora" two; the
        # engine asked for the count the resident had written (A–J of cycle 7).
        # "2 gr/24h" is a dose, and never gets here as red cells.
        found = [float(_UNIT_WORDS.get(count, count)) for count in re.findall(
            r"(?<![\w.])(\d+|una?|uno|dos|tres|cuatro|one|two|three|four)\s*gre?\b(?!\s*/)", body)]
        found += [1.0 for _ in re.finditer(r"\ban?\s+(?:single\s+)?unit\b", body)]
        found += [float(count) for count in re.findall(r"\bx\s*(\d+)\b", body)]
        if not found:
            bare = re.match(r"(\d)\s*(?:mas|more|adicional(?:es)?|extra|ahora|ya|now|stat)?\s*[.!]?$", body.strip())
            found = [float(bare[1])] if bare else []
    return found[0] if len(found) == 1 else None


# A red-cell order written as a chart line opens with its units, the product or
# what qualifies it, and says nothing else but when, where it runs and how fast:
# "2 U GR O negativo", "GR 2 U", "O-neg 2 units", "2 UGR", "2 PRBC now". With a
# red-cell word and a count anywhere in the clause enough, a result ("Hb 6.2 tras
# 2 U GR"), a transfusion elsewhere ("SAMU: 1 U GR O negativo en ruta"), a refusal
# ("rechaza transfusión de 2 U GR"), a question, a consent, an estimated loss and
# insulin written beside "blood glucose" each ran a transfusion nobody ordered
# (adversarial review of cycle 7). What opens as red cells and says more is asked
# about; what says it happened, or is only thought about, orders nothing.
_RED_CELL_OPENING = re.compile(
    r"(?:(?:\d+|una?|uno|one|two|three|four|five|six|dos|tres|cuatro|cinco|seis|single|an?)\s*(?:x\s*)?"
    r"(?:u\b\.?|units?\b|unidad(?:es)?\b|bolsas?\b|bags?\b|concentrad[oa]s?\b|paquetes?\b|p?rbcs?\b|ugr\b|"
    r"gre?\b|(?:" + _RED_CELL_NAMES + r")\b)"
    r"|(?:" + _RED_CELL_NAMES + r"|gre?|" + _BLOOD_WORD + r")\b"
    r"|(?:o|0)\s*(?:rh\s*)?-?\s*(?:neg|negativ|positiv|pos)\w*"
    r"|(?:uncross(?:ed|matched)|emergency[- ]release|type[- ]specific)\b)")
_RED_CELL_LINE_PART = re.compile(
    r"\b(?:" + _RED_CELL_NAMES + r"|gre?|sangre|blood|(?:blood\s+)?transfusi(?:on|ones))\b|"
    r"(?<![\w.])\d+(?:[.,]\d+)?(?![\w.])|\bx\s*\d+\b|\b(?:una?|uno|one|two|three|four|five|six|dos|tres|cuatro|cinco|"
    r"seis|single|x)\b|"
    r"\b(?:u|units?|unidad(?:es)?|bolsas?|bags?|concentrad[oa]s?|paquetes?|each|cada\s+una)\b\.?|c/u|"
    # "2u PRBC over 2h each", "en 2 hrs c/u": the count and the time (post hoc, blind set of cycle 8).
    r"(?<![\w.])\d+\s*u\b|\b(?:over|en|durante|in)\s+\d+(?:[.,]\d+)?\s*(?:h|hrs?|hours?|horas?|min(?:utes?|utos?|s)?)\b|"
    r"/\s*(?:h|hr|hora|hour)\b|\b(?:por|per)\s+(?:hora|hour)\b|"
    r"\b(?:de|of|del|the|las|los|la|el|more|mas|adicional(?:es)?|extra)\b|"
    r"\b(?:o|0)\s*(?:rh\s*)?-?\s*(?:neg|negativ[oae]s?|negative|pos|positiv[oae]s?|positive)\b|"
    r"\b(?:o|0)\s+rh\s*\(\s*[-+]\s*\)|(?<=\s)(?:o|0)\s*(?:rh\s*)?-(?=\s|$)|"
    # How it runs, and beside what: "to run now", "a pasar", "running together",
    # "juntas", "while the crossmatch is pending" (post hoc, blind set of cycle 7).
    r"\b(?:to\s+run|to\s+go|a\s+pasar|running(?:\s+together)?|together|juntas|juntos)\b|"
    r"\b(?:while|mientras)\b.*$|"
    r"\b(?:isogrupo|isorh|uncross(?:ed|matched)|emergency[- ]release|type[- ]specific|sin\s+cruzar|"
    r"no\s+cruzad[oa]s?|irradiad[oa]s?|irradiated|leucorreducid[oa]s?|leuko-?reduced|filtrad[oa]s?)\b|"
    r"\b(?:now|ya|ahora|stat|urgente|urgent(?:ly)?|inmediatamente|immediately|de\s+inmediato|right\s+now|asap|"
    r"back\s+to\s+back|seguidas?)\b|"
    r"\b(?:ev|iv|io|intravenos[oa]s?|intravenous|intraose[oa]s?|intraosseous|por\s+via\s+(?:periferica|venosa|"
    r"intraosea))\b|"
    r"\b(?:a\s+chorro|wide\s+open|rapid[oa]?|rapidly|fast|a\s+presion|under\s+pressure|"
    r"(?:with\s+(?:a\s+)?|con\s+)?(?:pressure\s+bag|manguito\s+de\s+presion|calentador|blood\s+warmer|"
    r"rapid\s+infuser))\b|"
    r"[():\-,.;!+/]")
# What says the units were given, elsewhere or before, or are only thought about.
_RED_CELL_HISTORY = re.compile(
    r"\b(?:given|received|transfused|administered|infused|recibid[oa]s?|recibi[oó]|pasad[oa]s?|transfundid[oa]s?|"
    r"administrad[oa]s?|already|previously|previ[oa]s?|prior|antecedentes?|history|s/p|status\s+post|"
    r"en\s+ruta|en\s+route|en\s+la\s+ambulancia|prehospital\w*|en\s+el\s+traslado|origen|outside|"
    r"otro\s+centro|lleva|llevaba|ha\s+recibido|hasta\s+ahora|so\s+far|total|balance|ingresos|intake|last|"
    r"ultim[oa]s?|semana\s+pasada|hace\s+\d|ago|mensual\w*|monthly|cronic\w*|chronic\w*|reacci[oó]n|reaction|"
    r"alergi\w*|allerg\w*|rechaz\w*|refus\w*|declin\w*|consent\w*|consentimiento|firm\w*|estimad\w*|"
    r"estimated|perdid\w*|loss|lost|needs?|need(?:ed|ing)|necesit\w*|requier\w*|requires?|requirio|threshold|"
    r"umbral|quedan)\b")
# What makes them a plan or an alternative, which is asked about, never run.
_RED_CELL_PLAN = re.compile(
    r"\b(?:cuando|when|once|en\s+cuanto|as\s+soon\s+as|apenas|until|hasta\s+que|after|despues|tras|post|"
    r"si|if|luego|then|later|mas\s+tarde|in\s+\d+\s*(?:min\w*|h|hours?)|en\s+\d+\s*(?:min\w*|h|horas?))\b")
# The verb of the bag itself, which is no order verb elsewhere: "hang packed
# cells now", "run 2 units", "cuelguen 2 U de GR" (A–J of cycle 7).
_BAG_VERB = re.compile(r"(?:hang|run|push|squeeze(?:\s+in)?|pump(?:\s+in)?|cuelg\w*|colg(?:ar|ue|uen|uemos)|"
                       # "Go to blood", "pasar a sangre": switching to blood is giving it.
                       r"(?:go|switch|move)\s+(?:over\s+)?to|(?:cambi(?:ar|a|o|en|emos)|pasemos)\s+a)\s+"
                       r"(?=(?:blood|sangre|p?rbcs?|globulos|gr\b|red\s+cells|packed)|\S+\s+(?:u|units?|unidad))|"
                       r"(?:blood\s+)?transfusi[oó]n\s+(?:de|of)\s+(?=\S)|(?:blood\s+)?transfusion\s+(?=\d)|"
                       r"(?:hang|run|push|squeeze(?:\s+in)?|pump(?:\s+in)?|cuelg\w*|colg(?:ar|ue|uen|uemos))\s+")
# The verbs whose object the red cells are when they give them.
_GIVES_RED_CELLS = {"give", "start", "administer", "infuse", "transfuse", "order", "want", "apply", "put",
                    "administrar", "administro", "administre", "dar", "doy", "dale", "iniciar", "inicio", "inicie",
                    "infundir", "transfundir", "transfundo", "poner", "pongo", "colocar", "coloco", "indicar",
                    "indico"}


def red_cell_line(body, strict=True, verb=None):
    """How a clause that opens with red cells reads: "order", "ask", "history", or None when red cells do not open it."""
    body = re.sub(r"^(?:(?:her|him|them|le|les|al\s+paciente|a\s+la\s+paciente|the\s+patient|the|la|las|los|"
                  r"el|una?(?!\s+(?:u\b|units?|unidad|bolsa|bag|paquete|concentrad|gre?\b))|another|otra|otras|otro|"
                  r"a(?=\s+(?:sangre|globulos|gr\b)))\s+)+(?=\S)", "",
                  str(body or "").strip())
    if not (_RED_CELL_OPENING.match(body) and red_cells_named(body, verb)) and not re.match(
            r"(?:\d+|una?|uno|one|two|three|four|dos|tres|cuatro|an?)\s*(?:u|units?|unidad(?:es)?)\b", body) and not (
            verb in {"transfuse", "transfundir", "transfundo"} and re.match(r"\d\b", body)):
        return None
    if _RED_CELL_HISTORY.search(body):
        return "history"
    if _RED_CELL_PLAN.search(body):
        return "ask"
    if not strict:
        return "order"
    return "order" if not _RED_CELL_LINE_PART.sub(" ", body).strip() else "ask"


def _stops(verb):
    return _operation(verb) == "stop" or verb in {"disconnect", "desconectar", "desconecta", "desconecto"}


def _red_cell_reading(text, body, verb, someone_elses, own=True):
    """(actions, verb) for red cells given now, asked about or not ordered; None when the clause is not their order."""
    lent_stop = not own and _stops(verb)
    if not own and verb not in _GIVES_RED_CELLS:
        # A verb the list lent is not this line's: "vía intraósea en tibia, GR O
        # negativo" lost the red cells to "place" (A–J of cycle 7).
        verb = None
    if lent_stop and re.match(r"(?:the|this|that|la|las|los|el|esta|este|esa|ese|dicha|dicho)\s", body):
        # What a stop lent to the list names is what it stops: "stop the
        # norepinephrine and the blood", "suspender el SF y los GR" (post hoc,
        # cycle 7). Quoted back, never run.
        return None
    switching = re.match(r"(?:over\s+)?(?:to|a)\s+(?=blood|sangre|p?rbcs?|globulos|gr\b|red\s+cells|packed)", body)
    if switching and own and verb in {"switch", "change", "cambiar"}:
        # "Switch to blood", "cambiar a sangre": switching to blood is giving it.
        verb, body = "give", body[switching.end():]
    # The verb of the bag is the clause's own, whatever the list lent it: "stop
    # the saline and go to blood" gave blood, never a stop.
    bag = _BAG_VERB.match(body)
    if bag:
        noun = "transfusi" in bag.group(0)
        if noun and (lent_stop or (own and verb and verb not in _GIVES_RED_CELLS and verb not in _DIAG_VERBS)):
            # "Transfusión de …" has no verb of its own: it is what the clause's verb
            # does. "Suspender transfusión de las 2 U GR", "stop transfusion of 2
            # units", "mantener transfusión de 2 U GR" and "suspender SF y
            # transfusión de 2 U GR" each ran the units they stopped or kept (post
            # hoc, cycle 7). They are quoted back, as before.
            return None
        verb, body = ("transfuse" if noun else "give"), body[bag.end():]
    if not red_cells_named(body, verb):
        return None
    line = red_cell_line(body, strict=not verb, verb=verb)
    if line is None:
        # Units asked to be kept, crossmatched or brought are asked about ("Tener
        # 4 U de GR disponibles", "Hold 2 units of PRBC", "Keep 2 units O-neg in
        # the room"). Otherwise red cells that do not open the clause are not its
        # object: "calcium gluconate 3 g IV after every 4 units of PRBC" is the
        # calcium.
        if (not someone_elses and _BLOOD_UNIT_COUNT.search(body) and not _RED_CELL_HISTORY.search(body)
                and (verb is None or verb not in _DIAG_VERBS)
                # "Reservar 2 unidades de GR", "grupo y pruebas cruzadas por 4 U":
                # the blood bank's request, read as the crossmatch it is below.
                and not re.search(r"\b(?:" + CROSSMATCH + r")\b", body)
                and (_RESERVING.search(body) or _FETCHING.match(body) or re.match(
                    r"(?:keep|tener|tengan|ten|dejar|dejen|deja|hold|cruz\w*|prepar\w*|reserv\w*)\b", body))):
            return [_clarification("Specify whether to transfuse these units now, with the number "
                                   "of units, or to request a crossmatch to have them reserved.")], verb
        return None
    if someone_elses or _NOT_THE_RESIDENTS_ORDER.search(body):
        return [], None
    if "?" in text or "\u00bf" in text or re.match(r"(?:should|shall|do|does|would|could|can|debo|deberia|"
                                                     r"deberiamos|hay\s+que)\b", text):
        # "¿Transfundo 2 U GR?", "Should I give 2 units O-neg?": a question.
        return [], None
    if line == "history":
        return [], None
    if verb and verb not in _GIVES_RED_CELLS:
        # "Pido 2 unidades de GR" asks the bank (below). A verb that gives no red
        # cells starts none, and the clause is read as whatever else it says, or
        # quoted back as before: returned as nothing, "stop the PRBC", "aplicar 2 U
        # GR" and "place 2 units of PRBC" were lost without a word (post hoc, cycle 7).
        return None
    if line == "ask" or _held_back(body, verb):
        return [_clarification("Specify whether to transfuse these units now, with the number "
                               "of units, or to request a crossmatch to have them reserved.")], verb
    return [{"type": "blood", "units": blood_units(body)}], verb


# What makes a product named in a clause something other than an order of it
# now: not needed, withheld, asked about, stopped, a threshold, chosen instead of
# something else, already given elsewhere, or being thawed or prepared. "FFP not
# needed", "Should we give FFP?", "Suspender PFC", "Give PCC 50 U/kg instead of
# plasma", "2 U PFC recibidas en ruta" and "Thaw 4 units FFP" were each recorded
# as a blood product ordered (adversarial review of cycle 7).
_NOT_A_PRODUCT_ORDER = re.compile(
    r"\b(?:not\s+(?:needed|indicated|required|necessary|the\s+priority)|no\s+(?:indicad[oa]s?|necesari[oa]s?|"
    r"requerid[oa]s?)|unnecessary|innecesari[oa]s?|withhold|hold\s+(?:off|the)|evitar|avoid|contraindicad\w*|"
    r"contraindicated|(?:has\s+)?no\s+role|instead\s+of|en\s+vez\s+de|en\s+lugar\s+de|rather\s+than|"
    r"stop|suspend\w*|deten\w*|discontinu\w*|threshold|umbral|"
    r"recibid[oa]s?|received|given|transfundid[oa]s?|transfused|administrad[oa]s?|en\s+ruta|en\s+route|"
    r"prehospital\w*|thaw\w*|descongel\w*|prepar\w*)\b|\?|\u00bf")
# A product's name used as the laboratory word it also is: "plasma lactate in 2
# h", "whole blood glucose 38", "platelets in 24 h", "plaquetas al día 5",
# "plasma K 2.9", "platelet count", "pérdida de sangre total".
_PRODUCT_AS_A_LAB = re.compile(
    r"\b(?:plasma|platelets?|plaquetas|whole\s+blood|sangre\s+total)\s+(?:lactate|lactato|glucose|glucosa|glicemia|"
    r"k|potassium|potasio|sodium|sodio|levels?|niveles?|count|conteo|recuento|free|libre|osmolal\w*|"
    r"(?:in|en)\s+\d|al\s+dia|daily|diari\w*|q\d|cada|control|monitoring|monitoreo)\b"
    r"|\b(?:perdida|loss|lost)\s+(?:de\s+)?(?:(?:sangre|blood)\b)|\bplatelet\s+count\b"
    r"|\b(?:glucosa|glicemia|glucose|lactato|lactate|potasio|potassium|sodio|sodium|hemoglobina|hb|niveles?|levels?)"
    r"\s+(?:en\s+|in\s+)?(?:sangre\s+total|whole\s+blood|plasma)\b")
_GIVES_A_PRODUCT = {"transfuse", "transfundir", "transfundo", "give", "administer", "infuse", "start",
                    "administrar", "administro", "administre", "dar", "doy", "dale", "infundir", "iniciar",
                    "inicio", "inicie", "poner", "pongo", "colocar", "coloco", "indicar", "indico", "order", "want"}


def unmodelled_blood_product(piece, verb=None, own=True):
    """The product a clause orders that the engine does not model, or None.

    Plasma, platelets, cryoprecipitate and whole blood are recorded as ordered,
    with their effect not modelled, and never become red cells (TD-26, B). A name
    that is also a laboratory word ("plasma", "platelets") is a product only when
    the clause gives or counts it, or the list transfuses: "plaquetas 45.000" is a
    result, and "Dar SF 1 L, plaquetas, INR" asks for a count. ``own`` is False
    when ``verb`` was lent by the list.
    """
    text = str(piece or "")
    if _RESERVING.search(text) and not (re.search(r"\btransf(?:und|us)\w*", text)
                                        or verb in {"transfuse", "transfundir", "transfundo"}):
        # A reservation, or units asked to be ready, gives nothing.
        return None
    if _NOT_A_PRODUCT_ORDER.search(text) or _PRODUCT_AS_A_LAB.search(text):
        return None
    named = re.search(r"\b(?:" + _PRODUCT_NAMES + r")\b", text)
    if named:
        return named.group(0)
    word = re.search(r"\b(?:" + _PRODUCT_WORDS + r")\b", text)
    giving = verb in {"transfuse", "transfundir", "transfundo"} or (own and verb in _GIVES_A_PRODUCT)
    if word and (giving or _GIVING_A_PRODUCT.match(text) or _PRODUCT_COUNT.search(text)):
        return word.group(0)
    return None


def massive_transfusion_activation(piece):
    """What is written after the massive transfusion protocol's activation, or None when not activated here.

    The activation is recorded and gives no product by itself (TD-26, C): the
    units given are the ones ordered. Only an activation is one: the protocol
    named first, or after a word that activates it. "May need massive
    transfusion", "MTP is likely", "call the blood bank for possible MTP", "MTP
    activated by the surgeon", "PTM ya activado" and the first MTP joint of an
    X-ray are not the resident activating it now (adversarial review of cycle 7).
    """
    text = str(piece or "").strip(" .,:;")
    named = _MASSIVE_TRANSFUSION.search(text)
    if not named:
        return None
    before = text[:named.start()]
    starts = re.fullmatch(r"(?:(?:please|por\s+favor|now|ahora|then|luego|and|y|(?:i|we)|(?:voy|vamos)\s+a|"
                          r"(?:the|an?|el|la|un)|protocolo\s+de|activaci[oó]n\s+del?|activation\s+of)\s+)*", before)
    if not starts and not (_ACTIVATING.search(before) and not re.search(
            r"\b(?:if|si|may|might|could|would|should|probably|likely|consider\w*|thinking|pensando|podr\w*|"
            r"necesit\w*|need\w*|prepar\w*|anticip\w*|habr\w*|hubier\w*|hubies\w*|deber\w*|had|"
            r"possible|posible|potential|potencial|eventual\w*|probable|standby|stand\s+by|"
            r"first|1st|primer\w*|second|segund\w*|x-?ray|radiograf\w*|rx|joint|articula\w*|toe|dedo|hallux)\b",
            before)):
        return None
    if re.search(r"\b(?:already|was\s+activated|had\s+been|ya\s+(?:se\s+)?activ\w*|ya\s+esta\s+activ\w*|"
                 r"fue\s+activad\w*|se\s+activo|activated\s+(?:at|by)|activad[oa]\s+(?:a\s+las|por))\b", text):
        return None
    after = text[named.end():]
    rest = after.strip(" ,.:;")
    if rest and not (_AFTER_THE_PROTOCOL.match(rest) or re.match(r"\s*:", after)):
        return None
    return rest


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

_A_QUESTION_TO_THE_PATIENT = re.compile(
    r"(?:\u00bf\s*)?(?:how|what|when|where|why|who|which|do\s+you|does\s+(?:it|he|she|the|this)|did\s+(?:you|it|he|she)|"
    r"are\s+you|is\s+(?:it|there|she|he|this)|have\s+you|has\s+(?:she|he|it)|any|como|que|cuando|donde|"
    r"por\s+que|tiene|tienes|siente|sientes|le\s+duele|te\s+duele|ha\s+tenido|has\s+tenido|hay\s+algo)\b")
# The purpose of a crossmatch is not a transfusion now: "grupo y pruebas cruzadas
# para transfundir 2 U GR" ran the units and lost the crossmatch (adversarial
# review of cycle 7).
_TO_TRANSFUSE = re.compile(r"\b(?:para|for|to|in\s+order\s+to)\s+(?:(?:poder|be\s+able\s+to)\s+)?"
                           r"(?:transfund\w*|transfus\w*|pas(?:ar|arlas?|arlos?)|give|dar(?:las?|los?)?|"
                           r"administr\w*)\b.*$")
# A study written as the whole order, with what may come around it: "UPT", "a
# quick UPT", "run a troponin", "beta-hCG stat". "Run a quick UPT" was lost
# without a word beside the adrenaline (TD-22, A–J of cycle 7).
# "Take" and "collect" are how a sample is asked for in English ("take blood cultures x2"), and
# a count or the sites are part of it: "hemocultivos x2", "blood cultures x2 from two separate
# sites" were lost without a word, alone or before the antibiotic (TD-30, cycle 8).
_A_STUDY_ALONE = (r"\s*(?:(?:run|draw|send\s+off|take|collect)\s+(?:(?:a|an|the|un|una|el|la)\s+)?"
                  r"(?:(?:quick|stat|urgent|rapid|rapido|rapida|urgente)\s+)?|"
                  r"(?:(?:a|an|the|un|una|el|la)\s+)?(?:quick|stat|urgent|rapid|rapido|rapida|urgente)\s+)?(?:{})"
                  r"(?:\s+(?:ahora|ya|now|stat|urgente|rapido|rapida|too|also|tambien)|\s*[x×]\s*\d|\s+\d\s*x\b|"
                  r"\s+(?:from|de|en)\s+(?:two|2|dos)\s+(?:separate\s+|different\s+|distintos\s+|diferentes\s+)?"
                  r"(?:sites|sitios|puntos|venas|veins)(?:\s+(?:distintos|diferentes))?|"
                  r"\s+(?:(?:two|2|dos)\s+(?:sets|frascos|muestras|samples))|\s+(?:bilaterales?|perifericos?|peripheral))*"
                  r"\s*\??")
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
# "Volver a" + an administration verb repeats that administration: "volver a
# nebulizar si persiste" is the next dose, not the patient coming back, and it
# was recorded as advice to the patient (DF-16b, 2026-09-28).
_ADMINISTRATION_INFINITIVES = (r"(?:nebulizar|administrar|dar|poner|pasar|repetir|iniciar|infundir|aplicar|"
                               r"inyectar|colocar|cargar|transfundir|cardiovertir|descargar|chocar|bolear)")
# How a discharge instruction is written, in both languages. The condition that
# follows one of these belongs to the advice, not to the order before it.
_ADVICE_CLAUSE = re.compile(
    r"\b(?:con\s+(?:indicaci[oó]n(?:es)?|instrucci[oó]n(?:es)?)\s+de|"
    r"con\s+control(?:\s+\w+)?\s+(?:en|a\s+las)|"
    r"indic[aáo]ndole\s+|indic(?:ar|o|ando)(?:le)?\s+(?=\w)|"
    r"with\s+instructions\s+to|advised\s+to|told\s+to|"
    r"safety[- ]net(?:ting)?|return\s+precautions?|"
    # The same advice without its preamble: "lo doy de alta y regresar si tiene
    # fiebre" lost the whole sentence, discharge included, in silence
    # (rehearsal of the twenty-scenario batch, 2026-09-25).
    r"(?:,\s*|(?:y|e|and)\s+)(?:que\s+|debe\s+|debera\s+|puede\s+|"
    r"le\s+(?:digo|explico|indico|pido)\s+que\s+)?"
    r"(?:regres(?:ar|e|a)|volver(?!\s+a\s+" + _ADMINISTRATION_INFINITIVES + r"\b)|vuelva|"
    r"reconsult(?:ar|e|a)|acud(?:ir|a)|return|come\s+back))\b", re.I)
# A condition on what the patient becomes, said with "when" as with "if": "When BP drops, give
# NS 500 mL", "cuando baje la PA, bolo de SF 500 mL" and "once glucose is below 70, give D50
# 50 mL" gave the dose now (TD-29, cycle 8). The clause is one only when it names a vital sign,
# a laboratory value or the patient with a change, a threshold or a state to be reached; or
# when what follows the word at once is the patient's course ("cuando empeore", "once
# stable"). What the team can do ("cuando puedas", "as soon as possible"), something awaited
# with no value to reach ("when blood arrives", asked about as before, "cuando vuelva el K"),
# a story ("when I examined him his BP was 80/50") and "en cuanto a" ("as to") are read as
# before. A result with the value it must reach is a condition: "when lactate comes back >4
# give 30 mL/kg LR", "en cuanto salga la troponina positiva" (post hoc, blind set of cycle 8). "Apenas" is
# one only before a verb in the subjunctive: in a note it is as often "barely" ("apenas mejora
# la PA") as "as soon as".
_WHEN_PARAMETER = (r"bp|blood\s+pressure|sbp|dbp|map|pressure|pa|pas|pad|pam|presion(?:\s+arterial)?|heart\s+rate|"
                   r"hr|pulse|fc|frecuencia(?:\s+cardiaca|\s+respiratoria)?|spo2|sats?|saturation|saturacion|"
                   r"oxygen(?:ation)?|oxigenacion|glucose|blood\s+sugar|bg|cbg|glucosa|glicemia|hgt|potassium|"
                   r"potasio|k|lactate|lactato|hb|hgb|hemoglobin|hemoglobina|platelets?|plaquetas|inr|temperature|"
                   r"temp|temperatura|fever|fiebre|rr|fr|respiratory\s+rate|gcs|glasgow|pain|dolor|urine\s+output|"
                   r"diuresis|ph|pco2|paco2|qrs|mental\s+status|consciousness|conciencia|he|she|patient|paciente|"
                   r"pt|condition|estado|cuadro|systolic|diastolic|sistolica|diastolica|peak\s+flow|pef|etco2|"
                   r"fingerstick|capillary\s+glucose|glicemia\s+capilar|sugar|dextro|mecanica(?:\s+ventilatoria)?|"
                   r"work\s+of\s+breathing|trabajo\s+respiratorio|sodium|sodio|creatinine|creatinina|"
                   r"bicarbonate|bicarbonato|hco3|troponin|troponina|"
                   # Post hoc, adversarial review of cycle 8: a parameter it did not list made the
                   # order run now ("D50 50 mL IV when FSBG < 60", "Transfuse 1 unit PRBC when Hct <
                   # 21"), and so did the course of the bleeding ("once hemostasis achieved").
                   r"fsbg|bgl|hct|hto|hematocrit|hematocrito|uo|pefr|symptoms?|sintomas?|bleeding|"
                   r"sangrado|hemorrhage|hemorragia|hemostasis|hemostasia")
_WHEN_STATE = (r"stable|estables?|stabili[sz]ed|estabilizad[oa]s?|unstable|inestables?|hypotensive|hipotens[oa]s?|"
               r"hypoxic|hypoxemic|hipoxemic[oa]s?|bradycardic|bradicardic[oa]s?|tachycardic|taquicardic[oa]s?|"
               r"awake|despiert[oa]s?|alert|conscious|consciente|worse|peor|febrile|febril|agitated|agitad[oa]s?|"
               r"in\s+shock|en\s+shock|hypoglyc(?:a)?emic|hipoglicemic[oa]s?|symptomatic|sintomatic[oa]s?|"
               # Post hoc, adversarial review of cycle 8: "Discharge home when afebrile x 24 h",
               # "Alta cuando esté asintomático", "Intubar cuando esté somnolienta" ran now.
               r"asymptomatic|asintomatic[oa]s?|afebrile|afebriles?|drowsy|somnolient[oa]s?|tired|"
               r"cansad[oa]s?|agotad[oa]s?|exhausted|symptom[- ]free|pain[- ]free|sin\s+dolor|sin\s+sintomas")
_WHEN_CHANGE = (r"\b(?:drops?|dropping|falls?|falling|decreases?|decreasing|goes\s+down|rises?|rising|increases?|"
                r"increasing|goes\s+up|climbs?|below|above|under|over|less\s+than|more\s+than|greater\s+than|"
                r"lower\s+than|higher\s+than|reach(?:es)?|baj(?:e|en|a|an)|ca(?:iga|igan|e|en)|disminuy\w*|"
                r"sub(?:e|a|an|en)|aument\w*|menor(?:es)?|mayor(?:es)?|sobre|alcance|persist\w*|worsen\w*|"
                r"deteriorat\w*|decompensat\w*|empeor\w*|descompens\w*|desatur\w*|improves?|improving|"
                r"mejor(?:e|a|en|an)|normali[zc]\w*|stabili[sz]\w*|estabili[zc]\w*|recover\w*|recuper\w*|"
                r"wakes?\s+up|despiert\w*|low|high|bajo|baja|alto|alta|positiv[oa]s?|positive|negativ[oa]s?|"
                r"negative|elevad[oa]s?|elevated|abnormal|alterad[oa]s?|"
                # Post hoc, adversarial review of cycle 8 ("when she tires", "once symptoms resolve",
                # "cuando se controle el sangrado").
                r"tires?|tiring|fatigues?|resolves?|resolved|resolving|resuelv(?:a|an)|ced(?:a|an)|subsides?|"
                r"controlled|controlad[oa]s?|se\s+controle|achieved|lograd[oa]|stops?|stopped|ces(?:e|en)|"
                + _WHEN_STATE + r")\b|[<>≤≥]")
# The clause the word opens ends at a comma, a colon or the next clause.
_WHEN_CLAUSE = r"(?:(?!\b(?:and|y|then|luego|pero|but)\b)[^,;:])"
_WHEN_COURSE = (r"(?:(?:se|le|lo|la)\s+)?(?:empeor\w*|descompens\w*|desatur\w*|deterior\w*|agrav\w*|mejore|mejoren|"
                r"estabilic\w*|normalic\w*|recuper\w*|despiert\w*|(?:(?:he|she|the\s+patient|pt|el\s+paciente|"
                r"la\s+paciente)\s+)?(?:(?:este|esten|esta|estan|se\s+encuentre|se\s+ponga|siga|is|becomes|gets|"
                r"remains)\s+)?(?:hemodynamically\s+|hemodinamicamente\s+)?(?:" + _WHEN_STATE + r")|"
                # Post hoc, adversarial review of cycle 8: "Intubar cuando se agote", "alta cuando
                # tolere VO", "alta una vez que complete 6 horas de observación" ran now.
                r"se\s+agot(?:e|en)|se\s+cans(?:e|en)|tolere[n]?\s+(?:la\s+)?(?:vo|via\s+oral|oral|alimentacion|"
                r"dieta|regimen)|tolerates?\s+(?:po|oral|diet|food|fluids)|(?:complete|completen|cumpla|cumplan)\s+"
                r"(?:(?:las?|sus?)\s+)?(?:\d+\s+horas?|observacion))\b")
# What makes the clause a description, not a condition (post hoc, adversarial review of cycle 8):
# what the team can do, the past, the resident or the team as its subject ("when I examine
# her she is hypotensive", "whenever we pause the fluids"), and in Spanish the indicative, since a
# condition is written in the subjunctive ("cuando baje la PA") while "cuando se acuesta la
# saturación cae a 85%" and "cuando la reevalúo la PA sigue baja" say what the resident saw.
_WHEN_DESCRIBES = (
    r"puedas|pueda|puedan|podamos|possible|posible|you\s+can|we\s+can|able|ready|listo|lista|listos|tengas|"
    r"tengamos|was|were|had|fue|estaba|estaban|tenia|arrived|llego|i|we|got|came|stood|laid|went|"
    r"examined|reassessed|released|paused|moved|transferred|"
    r"cae|caen|sube|suben|baj(?:a|an)\s+(?:a|de|hasta|bajo)|disminuye|disminuyen|aumenta|aumentan|persiste|"
    r"persisten|empeora|empeoran|mejora|mejoran|desatura|desaturan|sigue|siguen|tiene|tienen|venia|venian|llega|"
    r"llegan|llegaron|trasladaron|trasladamos|cayo|subio|empeoro|mejoro|desaturo|descompenso|evaluo|reevaluo|"
    r"examino|acostamos|acuesto|sentamos|paramos|retiramos|soltamos|suelto|movilizamos|movilizo|reviso|revisamos|"
    r"inicio|iniciamos|acuesta|sienta|levanta|marea|suelta|retira|se\s+pone")
# What the patient does, then what was measured when they did it: "when she talks her sats drop
# to 88%", "when he stands up his HR increases to 140". "Once she speaks in full sentences" is
# still a condition.
_WHEN_ACTIVITY_FINDING = (
    r"\b(?:he|she|they|the\s+patient|pt)\s+(?:talks?|speaks?|stands?|sits?|lies|walks?|ambulates?|moves?|"
    r"coughs?|eats?|gets?\s+up)\b" + _WHEN_CLAUSE + r"*?\d")
_WHEN_CONDITION = (
    r"(?:(?:when|whenever|as\s+soon\s+as|cuando|en\s+cuanto(?!\s+al?\b)|tan\s+pronto\s+como|una\s+vez\s+que)\b"
    r"(?!" + _WHEN_CLAUSE + r"*\b(?:" + _WHEN_DESCRIBES + r")\b)(?!" + _WHEN_CLAUSE + r"*?" + _WHEN_ACTIVITY_FINDING + r")"
    r"(?=" + _WHEN_CLAUSE + r"{0,60}?\b(?:" + _WHEN_PARAMETER + r")\b" + _WHEN_CLAUSE + r"{0,40}?(?:" + _WHEN_CHANGE
    + r")|" + _WHEN_CLAUSE + r"{0,40}?(?:" + _WHEN_CHANGE + r")" + _WHEN_CLAUSE + r"{0,40}?\b(?:" + _WHEN_PARAMETER
    + r")\b|\s+" + _WHEN_COURSE
    # A value compared with a number is a threshold whatever it is called: "when FSBG < 60",
    # "cuando T° > 38,5" (post hoc, adversarial review of cycle 8).
    + r"|" + _WHEN_CLAUSE + r"{0,40}?[<>≤≥]\s*\d)"
    # "Once" is also "one time" ("give it once more", "once again her pressure drops"): only the
    # patient's value or state right after it makes it a condition ("once his fingerstick
    # glucose drops below 70").
    r"|once(?!\s+(?:again|more|daily|a\s+day|only|weekly|a\s+week)\b)"
    r"(?!" + _WHEN_CLAUSE + r"*\b(?:" + _WHEN_DESCRIBES + r")\b)(?!" + _WHEN_CLAUSE + r"*?" + _WHEN_ACTIVITY_FINDING + r")"
    r"(?=\s+(?:(?:the|his|her)\s+)?(?:[a-z]+\s+){0,2}?(?:" + _WHEN_PARAMETER + r")\b" + _WHEN_CLAUSE
    + r"{0,40}?(?:" + _WHEN_CHANGE + r")|\s+" + _WHEN_COURSE + r"|" + _WHEN_CLAUSE + r"{0,40}?[<>≤≥]\s*\d)"
    # "Apenas" is "as soon as" only before what the patient is yet to do, in the subjunctive
    # ("apenas la HGT baje de 70"); before what the patient does it is "barely" ("apenas
    # mejora la PA con volumen").
    r"|apenas(?!" + _WHEN_CLAUSE + r"*\b(?:puedas|pueda|puedan|podamos|tengas|tenga|llegue|lleguen)\b)"
    r"(?=" + _WHEN_CLAUSE + r"{0,40}?\b(?:baje|bajen|caiga|caigan|suba|suban|disminuya|disminuyan|aumente|aumenten|"
    r"persista|persistan|empeore|empeoren|mejore|mejoren|desature|desaturen|descompense|descompensen|"
    r"normalice|normalicen|estabilice|estabilicen|recupere|recuperen|despierte|despierten|alcance|alcancen)\b))"
)
# How a service is written in a chart's shorthand (post hoc, blind set of cycle 8).
_SERVICE_ABBREVIATIONS = (r"uro|urolog\w*|cx|cirug\w*|cardio(?:logia)?|cards|gastro\w*|neuro(?:logia)?|nefro\w*|uci|upc|"
                          r"tox\w*|endocrino\w*|medicina\s+interna|hemodinamia|trauma(?:tologia)?|vascular")
# A clinical service by its name or its chart abbreviation: what "IC" must be followed by to be a
# consult, since "IC con FE preservada" is heart failure (post hoc, adversarial review of cycle 8).
_SERVICE_NAMES = (r"cardiolog\w*|cirug\w*|surgery|urolog\w*|gastro\w*|neurolog\w*|neurocirug\w*|nefrolog\w*|icu|"
                  r"traumatolog\w*|ortoped\w*|hemodinamia|infectolog\w*|neumolog\w*|broncopulmonar|hematolog\w*|"
                  r"toxicolog\w*|obstetric\w*|ginecolog\w*|psiquiatr\w*|pediatr\w*|anestesi\w*|otorrino\w*|"
                  r"oftalmolog\w*|dermatolog\w*|reumatolog\w*|oncolog\w*|geriatr\w*|inmunolog\w*|alergolog\w*|"
                  r"intensivo|intensivista|" + _SERVICE_ABBREVIATIONS)
# Services this simulator does not model as a consult, left as before the cycle (post hoc,
# adversarial review of cycle 8): "Social work consult, ceftriaxone 2 g IV" held the antibiotic.
_NON_CLINICAL_SERVICE = (r"social\s+work|sw|nutrition|dietitian|dietary|pharmacy|pharmacist|pt|ot|physical\s+therapy|"
                         r"occupational\s+therapy|case\s+management|chaplain|spiritual\s+care|trabajo\s+social|"
                         r"asistente\s+social|nutricion\w*|farmacia|farmaceutic\w*|kinesiolog\w*|kine|"
                         r"terapia\s+ocupacional")
# Advice to the patient that opens its own sentence: "Regresar si tiene fiebre", "Return if the
# pain comes back" (cycle 8). "Volver a nebulizar" is the next dose, "consultar a cirugía" and
# "return to the ward" are orders.
_RETURN_ADVICE = re.compile(
    r"(?:(?:y|e|and)\s+)?(?:que\s+|debe\s+|debera\s+|puede\s+|should\s+|to\s+)?"
    # "Volver a controlar creatinina si oliguria" repeats a check, and "consultar cirugía si persiste
    # el sangrado" calls a service (post hoc, adversarial review of cycle 8).
    r"(?:regres(?:ar|e|a)|volver(?!\s+a\s+(?!consultar\b)[a-z]+(?:ar|er|ir)\b)|vuelva|reconsult(?:ar|e|a)|"
    r"acud(?:ir|a)|consult(?:ar|e)(?!\s+(?:(?:a|al|con|de|el|la)\s+)?(?:" + _SERVICE_NAMES + r")\b)"
    r"(?!\s+(?:a|al|con|de)\b)|return(?!\s+to\s+(?:the\s+)?(?:ward|icu|unit|floor|"
    r"or|theatre|cath))|come\s+back|seek\s+(?:medical\s+)?(?:care|attention|help))\b")
# "If" and "si" after a verb of finding out are "whether": "check if she is pregnant", "evaluar
# si requiere intubación".
_WHETHER = re.compile(r"\b(?:check|see|ask|decide|determine|assess|evaluate|find\s+out|confirm|verify|know|"
                      r"decidir|decido|ver|veo|preguntar|pregunto|evaluar|evaluo|valorar|valoro|averiguar|"
                      r"confirmar|verificar|definir|saber|chequear)\s*$")
# Where an intramuscular injection goes, written on its own after it (TD-31, cycle 8).
_INJECTION_SITE = re.compile(
    r"(?:(?:in|into|to|on|at|en|al|a|el|la)\s+)*(?:(?:the|his|her|left|right|izquierd[oa]|derech[oa])\s+)*"
    r"(?:(?:antero)?lateral\s+thigh|mid[- ]?outer\s+thigh|outer\s+thigh|thigh|vastus\s+lateralis|deltoid|"
    r"cara\s+(?:antero)?lateral\s+del\s+muslo|cara\s+externa\s+del\s+muslo|muslo|vasto\s+(?:lateral|externo)|deltoides)"
    r"(?:\s+(?:muscle|musculo|anterolateral|lateral|izquierdo|derecho|left|right))*\s*[.!]?")
# A discharge said as a clearance where an order would start ("ok to dc home"; KD-05, cycle 8).
_OK_DISCHARGE_TAIL = re.compile(r"(?:ok(?:ay)?\s+(?:to|for|para)\s+)?(?:d/?c|discharge|dar\s+de\s+alta|alta)\b")
# The time red cells run in, as a clause of its own (post hoc, blind set of cycle 8).
_BLOOD_TIMING = re.compile(
    r"(?:(?:to\s+)?(?:administrar|pasar|run|give|infuse|infundir|transfundir|transfuse)\s+)?(?:en|over|durante|in)\s+"
    r"(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>h|hrs?|hours?|horas?|min(?:utes?|utos?|s)?)"
    r"(?:\s+(?P<each>c/u|each|cada\s+un[ao]|cada\s+unidad|per\s+unit|por\s+unidad))?\s*[.!]?")
# A regimen for home: how often and for how long (post hoc, blind set of cycle 8).
_HOME_REGIMEN = re.compile(
    r"\bc/\s*\d+\s*(?:h|hrs?|horas?)\b|\bcada\s+\d+\s*(?:h|hrs?|horas?)\b|\b(?:x|por|durante)\s*\d+\s*(?:d|dias?|días?|days?)\b|"
    r"\b\d+\s*(?:d|dias?|días?|days?)\b|\b(?:bid|tid|qid|qd|qhs|q\s*\d+\s*h|prn|sos|puffs?|inhalaciones)\b")
# The condition itself, so that what it conditions can be recognised.
# A colon closes a condition as a comma does: "si no responde: adrenalina 0.5 mg
# im" is a plan with its order, and was dropped without a word (DF-22, 2026-09-28).
_CONDITION_CLAUSE = re.compile(r"\b(?:if|si|unless|salvo\s+que|" + _WHEN_CONDITION + r")\b[^,:]*(?:[,:]|$)")
# A condition set between an order and its alternative: "atropina 1 mg ev, si no
# responde, marcapaso transcutaneo". What follows the condition is the plan.
_CONTINGENCY = re.compile(r"(?:if|si|unless|salvo\s+que|en\s+caso\s+de|" + _WHEN_CONDITION
                          + r")\b[^,:]*[,:]\s*(?P<then>\S.*)$")
# What a destination sends the patient with. After a discharge or an admission
# in the same sentence it is the plan that goes with them, not an order here:
# ", control urologico" held the whole submission as a study nobody could name
# (2026-09-25).
_DISCHARGE_ADVICE = re.compile(
    # An article may come first: "a follow-up appointment", "una cita" (DF-10).
    r"^(?:con\s+|with\s+)?(?:(?:a|an|un|una)\s+)?(?:control(?:es)?|seguimiento|citacion|cita|"
    # A referral goes home with the patient too (post hoc, adversarial review of cycle 8).
    r"(?:(?:[a-z]+\s+){0,2})?referral|derivacion|interconsulta|"
    r"signos?\s+de\s+alarma|indicaciones|"
    r"instrucciones|reposo|dieta|receta|educacion|follow[- ]?up|return\s+precautions?|"
    r"safety[- ]net(?:ting)?)\b"
    # English names the service first: "urology follow-up" was dropped where
    # "control urologico" was kept (EN/ES measurement, 2026-09-27).
    r"|^(?:with\s+)?(?:(?:a|an)\s+)?(?:[a-z]+\s+){1,2}(?:follow[- ]?up|appointment)\b")
# The plan a discharge is written with: "discharge him with orthopedic
# follow-up", "la doy de alta con control en policlinico". Each "with"/"con"
# may open it, and only what reads as advice is kept (DF-10).
_ATTACHED_PLAN = re.compile(r"\b(?:with|con)\s+")
# Safety-netting that lists what should bring the patient back. The list is the
# advice, so it runs to the end of the sentence instead of being cut at commas.
_LISTED_ADVICE = re.compile(
    r"\b(?:return\s+precautions?|safety[- ]net(?:ting)?(?:\s+advice)?|with\s+instructions\s+to|"
    r"advised\s+to|told\s+to|signos\s+de\s+alarma|senales\s+de\s+alarma)\b")
_CONDITIONAL = re.compile(
    r"\b(?:if|unless|consider|considering|might|could|would|perhaps|maybe|si|salvo que|considerar|considero|podria|quizas|tal vez)\b"
    r"|\b" + _WHEN_CONDITION
)
_NEGATION = re.compile(r"^(?:please\s+)?(?:do not|don't|dont|never|avoid|no|not|sin|evitar|evito)\b")
# What the resident finds, said with "no" or "sin": "sin acceso venoso visible",
# "no IV access", "no veo venas", "no tiene PA registrable", "sin pulso radial".
# It negates no order: read as a negation, it took the orders after it with it,
# and "sin acceso venoso visible, puyen una EZ-IO tibial ya" and "no tiene PA
# registrable, activemos el protocolo de transfusion masiva" were lost without a
# word (A–J of cycle 7, independent set).
_NEGATED_FINDING = re.compile(
    r"^(?:no|sin|without)\s+(?:"
    r"(?:(?:iv|intravenous|venous|peripheral|vascular|good|any|adequate)\s+)*access|"
    r"acceso(?:\s+(?:venoso|vascular|periferico|intravenoso))?|"
    r"(?:vias?|lineas?)\s+(?:venosas?|perifericas?|intravenosas?)|venas|veins|vvps?|ivs?|piv|"
    r"peripheral\s+ivs?|"
    r"(?:(?:radial|femoral|carotid|palpable|peripheral)\s+)?pulses?|"
    r"pulsos?(?:\s+(?:radial(?:es)?|femoral(?:es)?|perifericos?|palpables?))?|"
    # "No response:" and "sin mejoría" are the contingency of a plan, never a finding here.
    r"veo|encuentro|logro|consigo|hay|tiene|tengo|palpo|siento)\b")
# A repeat written after the order it repeats: "salbutamol 5 mg nbz, repetir
# cada 20 minutos si persiste el broncoespasmo", "epinephrine 0.5 mg IM, repeat
# in 5 minutes if no improvement". The order is given now; the repeat is a plan
# with its own interval, count and condition, and the condition belongs to the
# repeat, never to the order. The whole sentence used to be kept as one
# conditional plan: nothing ran, and the order was quoted back as the working
# model (DF-16b, 2026-09-28). A repeat with no interval, count or condition is a
# dose given again now ("repito salbutamol 5 mg nbz") and keeps that reading.
_REPEAT_START = re.compile(
    r"\b(?:(?:y|e|and|then|luego|despues)\s+)?(?:"
    r"(?:se\s+)?(?:puede|podria|pueden)\s+repetir(?:se|lo|la|los|las)?|"
    r"repetir(?:se|lo|la|los|las)?|repito|repita|repite|repitase|"
    r"volver\s+a\s+" + _ADMINISTRATION_INFINITIVES + r"|"
    r"(?:may|can|could)\s+(?:be\s+)?repeat(?:ed)?|to\s+be\s+repeated|repeat(?:ed)?|redose|re-dose)\b")
_REPEAT_UNIT = r"(min(?:utos?|utes?|s)?|h(?:oras?|ours?|rs?)?)\b"
_REPEAT_EVERY = re.compile(r"\b(?:cada|every|each|q|c/)\s*(\d+(?:\.\d+)?)\s*" + _REPEAT_UNIT)
_REPEAT_AFTER = re.compile(r"\b(?:en|in|a\s+los|after|tras|dentro\s+de|despues\s+de)\s+(\d+(?:\.\d+)?)\s*"
                           + _REPEAT_UNIT)
_REPEAT_NUMBERS = {"una": 1, "one": 1, "once": 1, "dos": 2, "two": 2, "twice": 2, "tres": 3, "three": 3,
                   "cuatro": 4, "four": 4}
# "Por 3 veces", "hasta 3 dosis", "x3", "up to 3 times", "once": the count
# needs its word, so "por 20 minutos" stays a duration.
_REPEAT_COUNT = re.compile(
    r"\bx\s*(\d+)\b|\b(?:por|hasta|up\s+to|maximo|max(?:imum)?(?:\s+of)?)\s+(\d+|una|dos|tres|cuatro|one|two|three|four)"
    r"\s+(?:veces|vez|times?|dosis|doses?)\b|\b(\d+|una|dos|tres|cuatro|one|two|three|four)\s+(?:veces|vez|times?)\b"
    r"|\b(once|twice)\b")
_REPEAT_CONDITION = re.compile(
    r"\b(?:si|if|mientras|while|hasta\s+que|until|unless|salvo\s+que|en\s+caso\s+de|prn|sos|"
    r"hasta\s+(?!(?:\d|una|dos|tres|cuatro)\b))")


def _minutes(match):
    value = float(match.group(1))
    return value * 60 if match.group(2).startswith("h") else value


def repeat_structure(clause):
    """Interval, count and condition of a repeat instruction: {} when it states none.

    Exported: the Management Trace and the validation tooling read the same
    structure the reader records.
    """
    verb = _REPEAT_START.search(clause)
    if verb is None:
        return {}
    before, after = clause[:verb.start()], clause[verb.end():]
    found = {}
    lead = re.match(r"\s*(?:if|si|unless|salvo\s+que|en\s+caso\s+de)\b[^,]*", before)
    tail = _REPEAT_CONDITION.search(after)
    scope = after[:tail.start()] if tail else after
    every = _REPEAT_EVERY.search(scope)
    later = None if every else _REPEAT_AFTER.search(scope)
    if every:
        found["every_min"] = _minutes(every)
    elif later:
        found["after_min"] = _minutes(later)
    count = _REPEAT_COUNT.search(scope)
    if count:
        word = next(group for group in count.groups() if group)
        found["count"] = int(word) if word.isdigit() else _REPEAT_NUMBERS[word]
    conditions = [text for text in ((lead.group(0).strip(" ,") if lead else ""),
                                    (after[tail.start():].strip(" ,.") if tail else "")) if text]
    if conditions:
        found["condition"] = "; ".join(conditions)
    return found


def _named_targets(text):
    """The studies, drugs and fluids a clause names, by their parser names."""
    names = {name for name, pattern in _DIAGNOSTICS.items() if re.search(r"\b(?:" + pattern + r")\b", text)}
    names |= {agent for agents in _AGENTS.values() for agent, pattern in agents.items()
              if re.search(r"\b(?:" + pattern + r")\b", text)}
    if re.search(r"\b(?:saline|ns|sf|ringer|ringers|lr|crystalloids?|cristaloides?|suero|fluids?|volumen|bolo|bolus)\b", text):
        names.add("fluid")
    return names


def _repeat_target(head, clause):
    """What a repeat written after an order repeats.

    "Salbutamol 5 mg nbz, repetir cada 20 minutos" repeats the salbutamol. "Activo
    hemodinamia y repito ECG en 10 minutos" names its own study, and it is not a
    repeat of the activation (DF-22, 2026-09-28).
    """
    verb = _REPEAT_START.search(clause)
    own = _named_targets(clause[verb.end():] if verb else clause)
    return head if not own or own & _named_targets(head) else None


def _repeat_split(sentence):
    """(what comes before, the repeat) when a repeat instruction closes the sentence."""
    for match in _REPEAT_START.finditer(sentence):
        prefix = sentence[:match.start()].rstrip()
        joined = re.match(r"(?:y|e|and|then|luego|despues)\s", match.group(0))
        if prefix and not prefix.endswith((",", ":")) and not joined:
            # "Order a repeat troponin": a repeat in the middle of an order is a word.
            continue
        head = re.sub(r"(?:,\s*)?\b(?:y|e|and|then|luego|despues)\s*$", "", prefix.rstrip(" ,:")).strip(" ,")
        clause = re.sub(r"^(?:y|e|and|then|luego|despues)\s+", "", sentence[match.start():].strip(" ,"))
        return head, clause
    return None


# What follows "si no responde," is an instruction whether or not this reader
# can execute it: "noradrenalina 0,1 mcg/kg/min, si persiste hipotenso, agregar
# vasopresina" keeps the norepinephrine now even though vasopressin is not read,
# and "..., si no responde, considerar intubacion" too (DF-22, C01). A second
# condition or a time ("si FC < 40, PA < 90"; "si no responde, a los 5 minutos")
# is no instruction, and the whole sentence stays the plan it was.
_INSTRUCTION_START = re.compile(
    r"(?:(?:y|e|and|then|luego|entonces)\s+)?"
    r"(?:(?:we|i|we'll|i'll|we\s+will|i\s+will|let's|let\s+us|vamos\s+a|voy\s+a|nos\s+vamos\s+a)\s+)?(?:"
    r"[a-z]+(?:ar|er|ir)(?:se|le|lo|la|les|los|las)?"
    r"|add|escalate|switch|change|consider|prepare|increase|decrease|raise|lower|double|halve|"
    r"call|page|notify|move|proceed|go|convert|upgrade|bump"
    r")\b")


def _opens_with_an_order(text):
    """Whether a reply is a new order rather than an answer to a held question.

    C07 lent the order verb a bare "I"/"we" ("I place a chest tube"). A reply
    such as "we start at 0.1 mcg/kg/min" answers a held rate question; read as a
    new order, it discarded the held bundle (adversarial review of cycle 6).
    """
    text = str(text or "")
    if re.match(r"(?:i|we)\s+(?!will\b|want\s+to\b|am\s+going\s+to\b)", text):
        return False
    return bool(_COMMAND.match(text))


def _an_instruction(text):
    text = str(text or "").strip(" ,.")
    # Chart shorthand is an instruction too: "si satura menos de 90%, mascarilla
    # con reservorio a 15 L/min" reads as an order once a verb is lent to it.
    return bool(text) and (_orders_now(text) or bool(_COMMAND.match(text)) or bool(_INSTRUCTION_START.match(text))
                           or _orders_now("start " + text) or _names_a_drug(text))


def _orders_now(text):
    """Whether this text, read alone, is an order: something given, done or indicated now."""
    parsed = parse_family_actions(text)
    return (any(action.get("type") not in {"clarification", "reassessment"} for action in parsed["actions"])
            or any(detail.get("kind") in {"not_modelled", "prescription"} for detail in parsed["future_details"]))
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
# An endoscopy asked for, alone or with a request verb: "Endoscopía urgente", "EDA urgente",
# "urgent upper endoscopy", "solicito EDA". Gastroenterology performs it in this simulator an
# hour after the call (family_engine, "endoscopy_after_consult_min"), so the request is the
# call; it was lost without a word or refused as an unknown study (TD-30, cycle 8). What was
# done ("EDA de ayer normal", "post-endoscopy") is not a request.
_ENDOSCOPY_REQUEST = re.compile(
    r"(?:(?:an?|una|la|the)\s+)?(?:(?:urgent|urgente|stat|early|precoz|emergent|emergency|de\s+urgencia)\s+)?"
    r"(?:upper\s+(?:gi\s+)?)?"
    r"(?:endoscop(?:y|ia)(?:\s+(?:digestiva\s+)?alta)?|eda|veda|egd|ogd|gastroscop(?:y|ia)|"
    r"videoendoscopia(?:\s+digestiva\s+alta)?)"
    r"(?:\s+(?:urgente|urgent|stat|now|ahora|ya|precoz|temprana|early|hoy|today|de\s+urgencia|asap|"
    r"as\s+soon\s+as\s+possible|lo\s+antes\s+posible|cuanto\s+antes))*"
    r"(?:\s+(?:para|for|to|por|re)\b.*)?\s*[.!]?"
    # "Urgent scope", "GI scope now": "scope" is the endoscopy only with its urgency or its
    # service; alone it is not (post hoc, blind set of cycle 8).
    r"|(?:(?:an?|the)\s+)?(?:(?:urgent|stat|early|emergent|emergency|gi|upper)\s+)+scope"
    r"(?:\s+(?:now|stat|today|tonight|urgently|asap))*(?:\s+(?:for|to|re)\b.*)?\s*[.!]?"
    r"|scope\s+(?:(?:him|her|the\s+patient)\s+)?(?:now|stat|today|tonight|urgently|asap)(?:\s+(?:for|to|re)\b.*)?\s*[.!]?")
_ENDOSCOPY_URGENCY = re.compile(r"\b(?:urgent|urgente|stat|now|ahora|ya|de\s+urgencia|precoz|temprana|early|emergent|"
                                r"emergency|hoy|today|tonight|asap|urgently|as\s+soon\s+as\s+possible|"
                                r"lo\s+antes\s+posible|cuanto\s+antes)\b")
_ENDOSCOPY_DONE = re.compile(r"\b(?:hace|ago|last|previous|previously|prior|previa|previo|anterior|antecedentes?|history|"
                             r"pmh|ayer|yesterday|showed|mostro|normal|done|realizad[oa]|hech[oa]|ligadura|banding|"
                             r"clipped|clips?)\b|:")
# A consult written as a noun on a chart line: "surgery consult", "GI consult re urgent EGD",
# "interconsulta a cirugía", "IC a urología ahora". Lost without a word (TD-30, cycle 8).
# "Per cardiology consult", "consult pending" and a consult already done are not a request.
_CONSULT_NOUN = re.compile(
    r"(?!(?:per|segun|according|after|tras|post|por|from|by|the|la|el)\b)(?!(?:" + _NON_CLINICAL_SERVICE + r")\s+)"
    r"(?:(?:urgent|stat|urgente|early|precoz)\s+)?(?:[a-z]+\s+){0,2}?(?:consult|consultation|referral)\b"
    r"(?!\s*(?:was|is|has|had|already|pending|done|requested|placed|called|note|recommend\w*|said|says))"
    r"|interconsulta\s+(?:a|al|con|to)\s+[a-z]"
    r"|ic\s+(?:a|al|con|to)\s+(?:(?:la|el)\s+)?(?:" + _SERVICE_NAMES + r")\b"
    # "IC uro", "IC cx vascular", "IC cardio": the chart's abbreviations (post hoc, blind set
    # of cycle 8). "IC descompensada" is heart failure, not a consult.
    r"|(?:interconsulta|ic)\s+(?:" + _SERVICE_ABBREVIATIONS + r")\b")
# What a consult written without a verb says has happened, or will not happen now (post hoc,
# adversarial review of cycle 8): "Surgery consult not needed at this time", "declined by patient",
# "deferred", "tomorrow", "GI consult in AM", "Surgery consult?", "saw pt", "appreciated", "IC a
# cirugía pendiente", "IC a cirugía: sin indicación quirúrgica". Each ran a consult.
_CONSULT_STATUS = re.compile(
    r"\b(?:not\s+(?:needed|indicated|required|necessary)|no\s+(?:need|operative|surgical|indication)|declined|refused|"
    r"deferred|tomorrow|in\s+(?:the\s+)?(?:am|morning)|saw|seen|appreciated|recs?|recommend\w*|following|aware|"
    r"on\s+board|signed\s+off|cleared|pending|pendientes?|respondid[oa]s?|realizad[oa]s?|solicitad[oa]s?|"
    r"en\s+curso|manana|sin\s+indicacion|no\s+requiere|evaluo|lo\s+vio|la\s+vio|ya)\b|\?|:\s*(?:no|sin)\b|"
    r"\s[-–—]\s*no\b")


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
    r"l(?:t|ts|iters?|itres?|itros?)?\b)(?!\s*/\s*(?:dl|l)\b)", re.I)
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
# Faculty decision 2 of 2026-09-25: a dose per kilogram is accepted for the
# medicines the engine supports, and weight_based_doses turns it into the dose
# with the patient's weight -- or asks for the weight and keeps the order.
_PER_KG_KINDS = _WEIGHT_BASED | {"anticoagulation", "steroid", "magnesium", "dextrose"}
_PER_KILO_ANY = re.compile(r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(mg|mcg|ug|g|gramos?|grams?|ui|u|units?|unidades)"
                           r"\s*/\s*kg(?!\s*/)", re.I)
#: Kinds whose dose field is in grams, so a dose per kilogram lands in grams too.
_GRAM_DOSE_KINDS = frozenset({"dextrose", "tranexamic_acid"})
#: How the record spells the unit of a dose per kilogram: the resident's amount
#: and unit, in the record's words ("80 UI/kg" is "80 units/kg", as the dose it
#: becomes is "3760 units"; units read the same in both languages, language.py).
_WRITTEN_UNIT = {"ug": "mcg", "ui": "units", "u": "units", "unit": "units", "unidades": "units",
                 "gram": "g", "grams": "g", "gramo": "g", "gramos": "g"}
# Faculty decision 4 of 2026-09-25: "dejar en observacion en urgencias N horas"
# is a destination, with its duration; keeping the patient monitored is not.
_ED_OBSERVATION = re.compile(
    r"\ben\s+observacion\b|\bunidad\s+de\s+observacion\b|\bobservacion\s+en\s+(?:el\s+servicio\s+de\s+)?urgencias\b"
    r"|\b(?:ed|emergency\s+department)\s+observation\b|\bobservation\s+unit\b"
    r"|\b(?:under|in)\s+observation\s+for\s+\d"
    # "Keep him under observation", "observe her in the ED": the English of "lo
    # dejo en observacion", a destination whose duration was not written.
    r"|\b(?:keep|leave|hold)\s+(?:him|her|them|the\s+patient)?\s*(?:under|in)\s+observation\b"
    r"|\bobserve\s+(?:him|her|them|the\s+patient)?\s*in\s+the\s+(?:ed|emergency\s+department)\b")
_ELSEWHERE = re.compile(r"\b(?:sala|ward|uci|icu|upc|intermedio|intermediate|coronaria|coronary|hospitaliz\w*|admit\w*)\b")
_OBSERVATION_HOURS = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:h|hrs?|horas?|hours?)\b")
_MONITOR_WORDS = re.compile(r"\bmonitor(?:izacion|izar|izado|eo)?\b|\boximetr[ií]a\b|\bpulse\s+ox")

_NOT_THE_RESIDENTS_ORDER = re.compile(
    r"\b(?:was|were|has\s+been|had\s+been|previously|already|got|gave|given|received|recibio|previamente|"
    r"en\s+route|prehospital\w*|pre-hospital\w*|in\s+the\s+(?:ambulance|field)|en\s+la\s+ambulancia|"
    r"medic|medics|paramedic\w*|paramedico\w*|ems|samu|"
    r"thinking|considering|wondering|pensando|pensaba|"
    r"no\s+corresponde|not\s+indicated|no\s+(?:esta|estan)\s+indicad\w*|contraindicad\w*|contraindicated)\b")
# What the prehospital team did goes on past "and"/"y": "medic already gave TXA
# 1 g over 10 min en route and put on a tourniquet", "el paramedico ya dejo 2 VVP
# y paso tranexamico 1 g en 10 minutos". The clause that names the team was set
# aside, and the one joined to it ran as the resident's order: a tourniquet and
# a second gram of tranexamic acid nobody ordered, once the duration of the drug
# was accepted (DF-22, C08; found by the blind held-out check, 2026-09-28).
# A later clause of that sentence, joined by "and"/"y" or with no order verb of
# its own, is asked about instead of run: it may still be the resident's order,
# and a question never loses it. The resident as its subject ("and I place",
# "y pongo") makes it the resident's order again, and so does a clause with the
# resident's own verb after a comma. An account is the team as the subject, told
# in the past: "remove the EMS dressing and apply a tourniquet" and "ask the
# medic what he gave and give naloxone" are the resident's orders (adversarial
# review of cycle 6). "Y coloco", "y paso" stay asked about: without its accent
# the verb is also the team's past ("colocó", "pasó").
_TXA_WORD = re.compile(r"\b(?:[aá]cido\s+tranex[aá]mico|tranexamic\s+acid|tranexamico|\btxa\b|exacyl|cyklokapron)\b")
_PREHOSPITAL_ACCOUNT = re.compile(
    r"^(?:(?:the|our|el|la|los|las|nuestro|nuestra|nuestros)\s+)?"
    r"(?:medic|medics|paramedic\w*|paramedico\w*|ems|samu|ambulance\s+crew|equipo\s+prehospitalario)\b"
    r"|^(?:en\s+(?:la\s+ambulancia|el\s+samu|el\s+traslado)|in\s+the\s+(?:ambulance|field)|en\s+route|"
    r"prehospital\w*|pre-hospital\w*)\b")
_TOLD_IN_THE_PAST = re.compile(
    r"\b(?:already|gave|given|got|put|placed|started|inserted|applied|administered|bagged|intubated|pushed|ran|"
    r"hung|did|was|were|had|ya|dio|dieron|puso|pusieron|paso|pasaron|dejo|dejaron|inicio|iniciaron|instalo|"
    r"instalaron|coloco|colocaron|administro|administraron|recibio|trajo|trajeron|intubo|intubaron|ventilo|"
    r"ventilaron)\b")
_RESIDENT_AS_SUBJECT = re.compile(
    r"^(?:(?:and|y|e|then|luego)\s+)?(?:i|i'll|i\s+will|i'm|i\s+am|we|we'll|we\s+will|let's|lets|yo|nosotros|"
    r"vamos\s+a|voy\s+a|nos\s+vamos\s+a|pongo|doy|pido|suspendo|transfundo|mido|repito|hago)\b")


def _part_of_an_account(piece):
    fragment = " ".join(str(piece).split())[:80]
    return {**_clarification(
        f'"{fragment}" is written with what the prehospital team did, so it was not given. If it is your '
        "order now, write it as your order, or say cancel. The other orders in this submission are held "
        "until then."), "account_text": fragment}


# A finding written after an order is what the resident sees, not a second
# order: "subele el oxigeno a reservorio a 15 L, satura 86% con la naricera" read
# the saturation as a nasal cannula adjustment with no flow and held the whole
# change (DF-22, C09, 2026-09-28). A vital sign with its value, and no order verb
# of its own, is a finding. "Mantener SpO2 > 94%" still has its verb.
_STATUS_FINDING = re.compile(
    r"^(?:(?:(?:el|la|the)\s+)?(?:paciente|patient|she|he|ella|el)\s+)?(?:"
    r"(?:satura|saturando|saturates|saturating|sats?|spo2|sato2|sat\s*o2|saturacion|saturation|"
    r"o2\s+sats?)\s*(?:(?:is|es|de|en|at|of|:|=|~|around|about|alrededor\s+de|cerca\s+de|"
    r"sigue\s+en|still|only|solo|apenas|just)\s*)*\d{2,3}\s*%?"
    r"|(?:pa|bp|presion(?:\s+arterial)?|blood\s+pressure|tas|tam|pam|map)\s*"
    r"(?:(?:is|es|de|en|at|of|:|=|~)\s*)*\d{2,3}\s*(?:/\s*\d{2,3})?(?:\s*mm\s*hg)?"
    r"|(?:fc|hr|frecuencia\s+cardiaca|heart\s+rate|pulso|pulse|fr|rr|frecuencia\s+respiratoria|"
    r"respiratory\s+rate)\s*(?:(?:is|es|de|en|at|of|:|=|~)\s*)*\d{1,3}"
    r"(?:\s*(?:lpm|bpm|rpm|x|x\s*min|/\s*min|por\s+minuto|per\s+minute))?"
    r")\b(?!\s*(?:mg|mcg|ug|g|ml|cc|l|lt|u|ui|units?|unidades|meq|mmol)\b)")


_WEIGHT_STATEMENT = re.compile(
    r"^(?:(?:el\s+|la\s+)?paciente\s+)?(?:pesa|peso(?:\s+(?:de|aproximado|estimado))?|weighs|weight(?:\s+(?:is|of))?)"
    r"\s*(?:(?:de|es|:|unos|aprox\.?|aproximadamente|about|around)\s*)*\d+(?:[.,]\d+)?\s*"
    r"(?:kg|kgs|kilos?|kilogramos?|kilograms?)?\s*$")
# A glucose written as the solution it comes in: "glucosa al 30% 50 ml", "D50 50 mL".
_SOLUTION_PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%|\bd(5|10|25|30|50)\b", re.I)
_SOLUTION_VOLUME = re.compile(r"(\d+(?:[.,]\d+)?)\s*(ml|cc|l|lt)\b", re.I)


def _per_kilo_order(kind, agent, match, text):
    """A dose per kilogram, kept as written: the weight turns it into a dose later."""
    value, unit = float(match[1]), match[2].lower()
    written = f"{value:g} {_WRITTEN_UNIT.get(unit, unit)}/kg"
    if unit in {"mcg", "ug"}:
        value, unit = value / 1000, "mg"
    if unit in {"ui", "u", "unit", "units", "unidades"}:
        field = "dose_units_per_kg"
    elif unit in {"g", "gram", "grams", "gramo", "gramos"}:
        field, value = ("dose_g_per_kg", value) if kind in _GRAM_DOSE_KINDS else ("dose_mg_per_kg", value * 1000)
    else:
        field, value = ("dose_g_per_kg", value / 1000) if kind in _GRAM_DOSE_KINDS else ("dose_mg_per_kg", value)
    # The record shows the dose as the resident wrote it ("1 mcg/kg"), whatever
    # unit the engine keeps it in.
    action = {"type": kind, "agent": agent, field: value, "route": _route(text), "per_kg_written": written}
    if kind in _GRAM_DOSE_KINDS:
        action.pop("agent")
    # "1.2 mg/kg de peso ideal": the weight type the resident named is kept with
    # the dose, and weight_based_doses uses it (faculty, 2026-09-27).
    basis = _weight_basis(text)
    if basis:
        action["weight_basis"] = basis
    return action


def _weight_basis(text):
    import patient_body
    return patient_body.basis_in(text)


_AMPOULE_COUNT = re.compile(r"\b(\d+|una|dos|tres|cuatro|one|two|three|four)\s+(?:ampollas?|amps?|ampoules?)\b")
_COUNT_WORDS = {"una": 1, "one": 1, "dos": 2, "two": 2, "tres": 3, "three": 3, "cuatro": 4, "four": 4}


def _ampoule_count(text):
    """How many ampoules an order names, or 1."""
    match = _AMPOULE_COUNT.search(str(text or "").lower())
    if not match:
        return 1
    word = match.group(1)
    return float(word) if word.isdigit() else float(_COUNT_WORDS[word])


def _dextrose_from_solution(text):
    """(grams, basis, percent, ml) for "glucosa al 30% 50 ml", or None: 30% x 50 mL = 15 g."""
    percent = _SOLUTION_PERCENT.search(text)
    volume = _SOLUTION_VOLUME.search(text)
    if not percent or not volume:
        return None
    share = float((percent.group(1) or percent.group(2)).replace(",", "."))
    ml = float(volume.group(1).replace(",", ".")) * (1000 if volume.group(2).lower() in {"l", "lt"} else 1)
    if not 0 < share <= 50 or not 0 < ml <= 1000:
        return None
    return round(share * ml / 100, 2), f"{share:g}% × {ml:g} mL", share, ml
_INFUSION_RATE = re.compile(r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(mg|mcg|ug)\s*/\s*(?:(kg)\s*/\s*)?(min|h|hr|hora|hour)\b", re.I)
_PER_KILO = re.compile(r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(mg|mcg|ug)\s*/\s*kg(?!\s*/)", re.I)


def _medication(text, kind, agent):
    dose, units = _amount(text, r"mcg|ug|mg|grams?|gramos?|g|units?|unidades|ui|u")
    if kind in _WEIGHT_BASED:
        infusion = _INFUSION_RATE.search(text)
        if infusion:
            rate = float(infusion[1]) / (1000 if infusion[2].lower() in {"mcg", "ug"} else 1)
            per_unit = ("mg/kg/" if infusion[3] else "mg/") + ("h" if infusion[4].lower().startswith(("h", "hora")) else "min")
            infusion_order = {"type": "sedation_infusion", "agent": agent, "rate": rate,
                              "units": per_unit, "route": _route(text) or "IV", "operation": "start"}
            if infusion[3] and _weight_basis(text):
                infusion_order["weight_basis"] = _weight_basis(text)
            return infusion_order
    if kind in _PER_KG_KINDS:
        per_kilo = _PER_KILO_ANY.search(text)
        if per_kilo:
            return _per_kilo_order(kind, agent, per_kilo, text)
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
        action = {"type": kind, "dose_g": mg / 1000 if mg is not None else None, "route": route}
        solution = None if action["dose_g"] is not None else _dextrose_from_solution(text)
        if solution:
            # Converted, and said so: the grams are the resident's solution, not a
            # dose the application chose (faculty decision 2, 2026-09-25).
            grams, basis, share, ml = solution
            count = _ampoule_count(text)
            if count > 1:
                # "2 ampollas de glucosa al 30% 20 mL cada una" is two ampoules, and
                # was read as one (2026-09-26). Without "cada una" the volume may be
                # the total or each, so the total is asked for, never guessed.
                if not re.search(r"\bcada\s+una\b|\bc/u\b|\beach\b", text):
                    return _clarification(
                        f"Write the total dextrose: the grams, or the concentration with the total "
                        f"volume. {count:g} ampoules with {ml:g} mL may mean {ml:g} mL in all or in each.")
                grams, basis = round(grams * count, 2), f"{count:g} × {share:g}% × {ml:g} mL"
                ml = ml * count
            action.update(dose_g=grams, dose_basis=basis, solution_percent=share, solution_ml=ml)
        return action
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
        # "6 ml/kg de peso real": the weight type named is kept (2026-09-27);
        # otherwise a volume per kilogram is on the predicted body weight.
        if _weight_basis(body):
            extras["tidal_weight_basis"] = _weight_basis(body)
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
# What an admission is written with: "admit to the ward on a D10 drip at 100
# mL/h", "ingreso a UCI con noradrenalina 0,1 mcg/kg/min". Only the destination
# was read, so the infusion the patient was admitted on never started and nothing
# said so (DF-22, C05, 2026-09-28). A complete treatment after "on", "con" or
# "with" is an order of its own. What cannot be given as written (no rate, no
# dose) or is not a treatment ("with hourly glucose checks", "con su esposa") is
# left as it was.
_ATTACHED_TREATMENT = re.compile(r"\b(?:on|con|with)\s+(?:(?:a|an|un|una)\s+)?(?=\S)")
# A monitored bed is part of where the patient goes, not an order of its own.
_NOT_A_TREATMENT = frozenset({"clarification", "diagnostic", "reassessment", "examination", "disposition",
                              "consult", "reperfusion_referral", "result_review", "monitoring"})
_QUANTITY = re.compile(r"\d+(?:[.,]\d+)?\s*(?:mg|mcg|ug|g|ml|l|u|ui|units?|unidades|meq|mmol|%)\b")
# "Hold NS, O2 4 L NC" stopped the oxygen too: the stop verb was lent to the
# next item of the list, which took the patient off oxygen (found by the
# adversarial review of cycle 6; "suspender SF, O2 4 L NC" did the same before).
# An item that names its own dose, volume or flow is a new order, not one more
# thing to stop; "suspender SF y noradrenalina" and "stop the saline and the
# 500 mL bolus" still stop both.
_STOP_VERBS = frozenset({"stop", "discontinue", "suspender", "suspendo", "detener", "retirar", "retiro", "sacar",
                         "saco", "desconectar", "desconecta", "desconecto", "disconnect"})
_DETERMINER_START = re.compile(r"(?:the|el|la|los|las|that|this|ese|esa|este|esta|su|sus|his|her|its)\b")
# Nor is it lent to what is said about the patient: "turn off the maintenance
# fluids, she's wet, and switch to a nitro drip" read "stop she's wet" and held
# the change as an unrecognized order.
_PATIENT_STATEMENT = re.compile(
    r"(?:she|he|they|the\s+patient|patient|pt|ella|el\s+paciente|la\s+paciente|paciente)\s*"
    r"(?:'s|'re|is|are|was|were|esta|estan|sigue|siguen|tiene)\b")


# "With a norepinephrine infusion ready" is prepared, not started.
_NOT_STARTED_YET = re.compile(
    r"\b(?:ready|prepared|available|on\s+standby|standby|at\s+the\s+bedside|to\s+hand|if\s+needed|"
    r"lista|listas|listo|listos|preparad[oa]s?|disponibles?|a\s+mano|en\s+espera|por\s+si)\b")


def _attached_treatment(body):
    for count, match in enumerate(_ATTACHED_TREATMENT.finditer(body)):
        if count >= 4:
            # Each try parses the rest of the clause: a long run of "on x" was
            # quadratic (adversarial review of cycle 6).
            break
        attached = body[match.end():]
        if _NOT_STARTED_YET.search(attached):
            continue
        parsed, _ = _parse_piece("start " + attached)
        # Whatever treatment is written with the destination goes with it,
        # quantified or not: "admit to the ICU on continuous albuterol 10 mg/h",
        # "transfer to the CCU on transcutaneous pacing at 80 bpm" and a heparin
        # infusion were dropped without a word, because only a few dose fields
        # counted (DF-22, C05; found by the blind held-out check, 2026-09-28).
        treatments = [action for action in parsed if action.get("type") not in _NOT_A_TREATMENT]
        if treatments:
            return treatments
        # A medicine the reader cannot run as written is asked about, never
        # dropped. "With his wife" names no medicine and asks nothing.
        questions = [action for action in parsed if action.get("type") == "clarification"]
        if questions and (_names_a_drug(attached) or _QUANTITY.search(attached)):
            return questions
    return []


def _parse_piece_core(piece, inherited=None):
    # "Preparo intubacion", "preparo la intubacion", "preparo todo para intubar":
    # the first person and the article dropped the order in silence (2026-09-25).
    if re.fullmatch(r"\s*(?:(?:i|we)\s+(?:will\s+|am\s+going\s+to\s+|are\s+going\s+to\s+)?|i'll\s+|we'll\s+)?"
                    r"(?:prepare|prep|set up|get ready|preparar|prepara|preparo|preparamos)"
                    r"(?:\s+(?:for|para))?(?:\s+(?:la|el|todo\s+para|to|the|an?))?"
                    r"\s+(?:intubation|intubacion|intubar|intubate|airway|via aerea|rsi|"
                    r"rapid\s+sequence\s+(?:intubation|induction))\s*[.!]?", piece):
        return [{"type": "airway_preparation"}], "prepare"
    text = piece.strip(" :")
    # "Meanwhile NS 500 mL bolus", "mientras tanto RL 500 ml" (post hoc, blind set of cycle 8).
    text = re.sub(r"^(?:please|por favor|then|luego|despues|meanwhile|in\s+the\s+meantime|mientras\s+tanto|entretanto|"
                  r"en\s+el\s+intertanto)\s+", "", text)
    if _MONITOR_ORDER.fullmatch(text):
        # The monitor itself (DF-16a). The verb still reaches the items after
        # it, so "monitorizar, PA y FC" keeps watching what it names.
        return [{"type": "monitoring", "operation": "start"}], "monitor"
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
    if vital and vital.group(0) == "oxigeno" and (
            re.search(_FLOW, body) or any(re.search(r"\b(?:" + pattern + r")\b", body)
                                          for name, pattern in _OXYGEN_DEVICES if name != "room air")):
        # Oxygen with a device or a flow is given, not watched: under the verb
        # of a "monitor" before it in a list, "oxígeno por mascarilla a 8
        # L/min" became a check of the saturation (DF-16a, 2026-09-28).
        vital = None
    if observational and vital:
        delay, _ = _amount(body, r"minutes?|mins?|minutos?")
        if re.search(r"\b(?:hours?|horas?|seconds?|segundos?)\b", body):
            return [_clarification("Specify the reassessment interval in minutes.")], verb
        return [{"type": "reassessment", "delay_min": delay if delay is not None else 0}], verb if verb in _DIAG_VERBS else "monitor"
    if re.search(r"\b(?:saturation|saturacion|spo2|sats|oxygen levels)\b", body) and not re.search(_FLOW, body) and verb in {"increase", "decrease", "set", "aumentar", "disminuir", "ajustar"}:
        return [_clarification("An oxygen saturation target is not a device or flow order. Specify the oxygen device and flow to administer.")], verb
    # "Activate MTP and transfuse": a transfusion with nothing named is asked
    # about -- which product, how many units -- and never read as nothing (TD-26).
    if not body and verb in {"transfuse", "transfundir", "transfundo"}:
        return [_clarification("Specify which blood product to give and how many units.")], verb
    # A bare "hospitalizalo" or "dale de alta" is a real disposition order with a
    # question attached, not nothing at all (2026-09-21).
    if not body and verb not in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar",
                                 "intubate", "intubar", "intubo",
                                 "admit", "transfer", "discharge", "hospitalizar", "ingresar", "trasladar"}:
        return [], verb

    # "...with RR 32 and more effort" describes the patient: "more" repeats a
    # treatment only after an order verb or beside something that can be given
    # (the twenty scenarios in English, 2026-09-25). "Mas esfuerzo" never
    # reached here, since "mas" does not start a repeat.
    if (not verb and re.match(r"(?:another|more)\b", body)
            and not re.search(r"\b(?:bolus|fluids?|saline|ns|ringers?|lr|crystalloids?|ml|cc|dose|doses|mg|mcg|"
                              r"units?|oxygen|o2|blood|units?)\b", body)
            and not _names_a_drug(body)):
        return [], None
    if verb in {"repeat", "repetir", "repito", "repite"} or re.match(r"(?:another|more|otro|otra|otros|otras)\b", body):
        studies = [name for name, pattern in _DIAGNOSTICS.items() if re.search(r"\b(?:" + pattern + r")\b", body)]
        if studies:
            return [{"type": "diagnostic", "diagnostic": name} for name in studies], verb
        quantity_text = re.split(r"\b(?:over|durante|en)\s+[-.\d]", body)[0]
        if len(re.findall(r"(?<![\w.])-?(?:\d+(?:\.\d+)?|\.\d+)\s*(?:ml|cc|l|lt|mg|g|mcg|ug)\b", quantity_text)) > 1:
            return [_clarification("Specify one quantity for the treatment to repeat.")], verb
        target = "fluid" if re.search(r"\b(?:bolus|fluid|saline|ns|sf|ringer|ringers|lr|crystalloid|cristaloides?|bolo|suero|ml|cc)\b", body) else None
        agent = next((name for agents in _AGENTS.values() for name, pattern in agents.items() if re.search(r"\b(?:" + pattern + r")\b", body)), None)
        if target is None and agent is None and re.search(r"\b(?:adrenalina|epinefrina|epinephrine|adrenaline)\b", body):
            # Adrenaline is read by its route, not by a name: "repito la adrenalina
            # 0.5 mg im" repeats the intramuscular dose, a bolus repeats a bolus.
            target = "epinephrine_bolus" if _route(body) == "IV" else "epinephrine_im"
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

    # What was done before, by someone else, or only thought about, is not an
    # order. The bleeding measures and tranexamic acid below are read anywhere in
    # the piece, so without a verb of the resident's they first pass the same
    # test every other medicine passes at the gate: "medic already gave TXA 1 g
    # en route", "estaba pensando en dar tranexamico", "no corresponde acido
    # tranexamico" ran the drug once its duration was accepted (DF-22, C08;
    # found by the blind held-out check, 2026-09-28).
    # Every other medicine passes the history test at the verbless gate below;
    # returning here for every piece silently dropped "paracetamol 1 g ev ya que
    # AINE contraindicado" and held "epinephrine 0.5 mg IM given anaphylaxis"
    # (adversarial review of cycle 6).
    someone_elses = not verb and bool(_NOT_THE_RESIDENTS_ORDER.search(body))

    # The x of xABCDE. A tourniquet, direct pressure and packing are the three
    # measures this engine performs, and each names where it is applied. Each
    # measure written is its own order, in the order written, and none becomes
    # another: "direct pressure with packing" ran as packing alone. "Pack the
    # wound", "hold pressure" and "presión sobre la herida" were lost without a
    # word, and "descartar taponamiento cardíaco" packed a wound (C7-06).
    measures = _haemorrhage_measures(text, verb)
    if not measures and not someone_elses and _MEASURE_NAMED.search(text) and (
            _REMOVING_A_MEASURE.match(text) or _stops(verb)) and not _STOPPING_THE_BLEEDING.search(text):
        # "Remove the tourniquet", "loosen the tourniquet to check for bleeding",
        # "convert tourniquet to pressure dressing": the engine neither removes nor
        # converts a measure, and each was lost without a word once it no longer
        # applied the measure it removed (post hoc, cycle 7). Quoted back.
        return [_unreadable(piece)], verb
    if measures and not someone_elses:
        site = ("limb" if re.search(r"\b(?:extremidad|pierna|brazo|muslo|antebrazo|limb|leg|arm|thigh|"
                                    r"forearm|miembro)\b", body)
                else "wound")
        return [{"type": "hemorrhage_control", "measure": measure, "site": site,
                 **({"named": named} if named else {})} for measure, named in measures], verb or "apply"

    if not someone_elses and re.search(r"\b(?:faja\s+p[eé]lvica|cintur[oó]n\s+p[eé]lvico|pelvic\s+binder|"
                                       r"binder\s+p[eé]lvico|sabana\s+p[eé]lvica|pelvic\s+(?:sheet|wrap))\b", body):
        return [{"type": "pelvic_binder"}], verb or "apply"

    # An intraosseous line is its own access, recorded as the resident placed it
    # and never as an intravenous one: "humeral IO" was lost without a word, and
    # "place a tibial IO" was quoted back as unreadable (C7-06). A clause that
    # also gives a medicine or a fluid is that order, given by the IO route.
    placing = verb in {"place", "insert", "put", "get", "start", "obtain", "colocar", "coloco", "poner", "pongo",
                       "obtener"} and bool(_PLACING_IO.match(body))
    if not someone_elses and (_IO_ACCESS.search(text) or placing
                              or re.search(r"\b(?:io|intraosseous|intraose[ao])\b", body)) and (
            _operation(verb) == "stop" or re.match(r"(?:remove|pull|take\s+out|discontinue|retir\w*|sac\w*|quit\w*)\b",
                                                   text)):
        # "Remove the humeral IO", "retirar la vía intraósea": a removal, recorded as one (adversarial review).
        return [{"type": "vascular_access", "operation": "stop", "access": "intraosseous"}], verb or "remove"
    if (_IO_ACCESS.search(text) or placing) and _IO_STATUS.search(text):
        # "The humeral IO is infiltrated", "IO access failed, place a second
        # peripheral IV": what the line is doing, never a line placed.
        return [], None
    # What the line is for is not given through it: "place humeral IO for fluids"
    # lost the line to a fluid with no volume (post hoc, cycle 7).
    purpose = re.sub(r"\s+(?:for|para)\s+(?:(?:the|los|las|el|la)\s+)?(?:fluids?|volumen|volume|fluidos|"
                     r"resuscitation|reanimacion|blood|sangre|drugs|medications|farmacos|medicamentos)"
                     r"(?:\s+(?:and|y)\s+(?:fluids?|volumen|volume|fluidos|blood|sangre|drugs|farmacos))?\s*[.!]?$",
                     "", body)
    if not someone_elses and (_IO_ACCESS.search(text) or placing) and not _names_a_drug(purpose) and not re.search(
            r"(?<![\w.])\d+(?:\.\d+)?\s*(?:mg|mcg|ug|g|ml|cc|l|u|units?|unidades?)\b|"
            r"\b(?:saline|ns|sf|ringer|lr|crystalloid|cristaloides?|suero|fluids?|bolus|bolo)\b", purpose):
        site = ("humeral" if re.search(r"\b(?:humer\w*|shoulder|hombro)\b", body)
                else "tibial" if re.search(r"\b(?:tibi\w*|shin)\b", body)
                else "sternal" if re.search(r"\b(?:stern\w*|esternal)\b", body)
                else "femoral" if re.search(r"\b(?:femoral|femur|femoris)\b", body) else None)
        return [{"type": "vascular_access", "operation": "start", "access": "intraosseous",
                 **({"site": site} if site else {})}], verb or "place"

    # Red cells, read before anything else can take their count: given now, asked
    # about, or not ordered at all (TD-26; adversarial review of cycle 7).
    red = _red_cell_reading(text, body, verb, someone_elses, own=bool(command))
    if red is not None:
        return red

    txa = _TXA_WORD.search(body)
    # Like any other medicine, without a verb it is an order only where it opens
    # the piece, or its dose does: "TXA 1 g IV", "1 g TXA IV". A route, an
    # article or "urgent" may come first, as for any other medicine: "IV TXA 1
    # g", "el ácido tranexámico 1 g ev", "urgent TXA 1 g IV" were held.
    if txa and not someone_elses and (
            verb or re.match(r"\d", body)
            or re.fullmatch(r"(?:(?:iv|ev|io|el|la|the|an?|urgent[e]?|stat|now|ahora)\s+)*", body[:txa.start()])):
        # "15 mg/kg" is a dose per kilogram; until 2026-09-26 the fixed-dose
        # pattern read it as 15 mg and the range check then refused it.
        per_kilo = _PER_KILO_ANY.search(body)
        if per_kilo:
            order = _per_kilo_order("tranexamic_acid", None, per_kilo, body)
            order["route"] = order.get("route") or "IV"
            return [order], verb or "give"
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
    # Two studies in the order they are to be done: "prueba de embarazo antes del
    # angioTAC", "pregnancy test before CT". Neither was read (TD-22, adversarial
    # review of cycle 7).
    ordered = re.split(r"\s+(?:antes\s+del?|before(?:\s+the)?|previo\s+al?|y\s+luego|and\s+then)\s+", body)
    if not verb and len(ordered) == 2:
        named = [next((name for name, pattern in _DIAGNOSTICS.items()
                       if re.fullmatch(_A_STUDY_ALONE.format(pattern), part)), None) for part in ordered]
        if all(named):
            return [{"type": "diagnostic", "diagnostic": name} for name in named], "order"
        if named[0] and re.search(r"\b(?:ct|tc|tac|scan|x-?ray|rx|radiograf\w*|angio\w*|eco\w*|ultrasound|mri|rm|"
                                  r"resonancia|imaging|imagen)\b", ordered[1]):
            # "Pregnancy test before CT": the test, and the study not named enough
            # to request, asked about.
            return [{"type": "diagnostic", "diagnostic": named[0]},
                    _clarification("The requested study was not recognized. Specify one supported study per order.")
                    ], "order"
    diagnostics = []
    for diagnostic, pattern in _DIAGNOSTICS.items():
        match = re.search(r"\b(?:" + pattern + r")\b", body)
        if diagnostic == "chest_xray" and other_region and not re.search(r"\btorax\b|\bchest\b", body):
            continue
        # A crossmatch is asked for without a study verb as often as with one
        # ("reservar 2 unidades", "grupo y pruebas cruzadas"). Only a verb that
        # gives the blood makes the sentence a transfusion instead.
        # "Type and cross pending", "pruebas cruzadas en curso": where the crossmatch is, not
        # one asked for (TD-32, cycle 8).
        # Its purpose is no state: "Type and cross 4 units to be ready for the OR", "…2 units awaiting OR"
        # and "…4 units sent stat" ask for it (post hoc, adversarial review of cycle 8).
        crossmatch = (diagnostic == "crossmatch" and match and not _TRANSFUSING.search(_TO_TRANSFUSE.sub(" ", text))
                      and not re.search(r"\b(?:pending|pendientes?|en\s+curso|in\s+(?:process|progress)|processing|"
                                        r"procesando|en\s+proceso|sent(?!\s+(?:stat|now|asap|urgently))|"
                                        r"enviad[oa]s?(?!\s+(?:urgente|ahora|ya))|already|ya\s+(?:fueron|estan|se)|"
                                        r"(?<!to\s)(?<!be\s)(?<!para\s)(?:listas?|listos?|ready)|done|hech[oa]s?|"
                                        r"realizad[oa]s?|tomad[oa]s?|solicitad[oa]s?|drawn|"
                                        r"(?:awaiting|esperando)(?=\s+(?:the\s+|el\s+|los\s+)?(?:results?|resultados?|"
                                        r"blood\s+bank|banco))|resulted|disponibles?)\b", body))
        if match and (verb in _DIAG_VERBS or crossmatch
                      or re.fullmatch(r"\s*(?:" + pattern + r")(?:\s+(?:ahora|ya|now|stat|urgente))?\s*\??", body)
                      or (not verb and re.fullmatch(_A_STUDY_ALONE.format(pattern), body))):
            diagnostics.append((match.start(), {"type": "diagnostic", "diagnostic": diagnostic}))
    if diagnostics:
        return [action for _, action in sorted(diagnostics, key=lambda x: x[0])], verb or "order"
    # Asking which gases is right when the resident asked for gases. "Los gases
    # muestran retencion de CO2" is a result they are reading, not an order, and
    # it held a whole escalation to non-invasive ventilation (2026-09-24).
    # "Blood gases?" read "blood gase" or "blood gases": "a blood gas" was never matched (cycle 8).
    if re.search(r"\b(?:gases|gasometria|blood\s+gas(?:es)?)\b", body) and (
            verb in _DIAG_VERBS or re.fullmatch(r"\s*(?:(?:take|draw|send|run|collect)\s+)?(?:(?:los|unos|the|a|an)\s+)?"
                                                r"(?:gases|gasometria|blood\s+gas(?:es)?)\s*\??", body)):
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
        if (re.search(r"\b(?:unidades?|units?|u)\b", body) or _BLOOD_UNIT_COUNT.search(body)) and red_cells_named(body):
            return [_clarification("Specify whether to transfuse these units now, with the number "
                                   "of units, or to request a crossmatch to have them reserved.")], verb
        # "Send her home" and "get IV access": English verbs that also ask for a
        # study, with none after them. They were refused as unknown studies, and
        # a discharge written that way held the whole order (the twenty scenarios
        # in English, 2026-09-25).
        if verb == "send" and re.search(r"\bhome\b", body):
            return [{"type": "disposition", "destination": "home"}], verb
        support = _support_order(body, verb)
        if support is not None:
            return [support], verb
        if _ENDOSCOPY_REQUEST.fullmatch(body) and not _ENDOSCOPY_DONE.search(body):
            return [{"type": "consult", "service": "gastroenterology"}], verb
        return [_clarification("The requested study was not recognized. Specify one supported study per order.")], verb

    if not verb:
        shorthand = r"(?:sf|ns|sg|suero\s+glucosado|glucosado|solucion\s+glucosada|suero\s+fisiologico|solucion\s+fisiologica|ringer(?:\s+lactato)?|lr|cristaloides?|synchronized cardioversion|synchronized shock|choque sincronizado|cardioversion|bipap|cpap|niv|vni|vmni|intubation|intubacion|bag[- ]mask|bag[- ]valve[- ]mask|bvm|ambu|oxygen|oxigeno|o2|nasal cann?ula|canula nasal|naricera|nc|non[- ]rebreather|nrb|room air|aire ambiente|dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|epinephrine|epinefrina|adrenaline|adrenalina|nitroglycerin|nitroglicerina|nitro|needle decompression|needle thoracostomy|finger thoracostomy|chest tube|thoracostomy|descompresion con aguja|descompresión con aguja|puncion pleural|punción pleural|tubo pleural|pleurotomia|pleurotomía|continuous monitoring|monitorizacion continua|cardiac monitor|monitor cardiaco)"
        # A route written first is how the order is spoken in English: "IM
        # adrenaline 0.5 mg", "IV morphine 4 mg", "oral paracetamol 1 g". The
        # route is not the order, so it is stepped over rather than made one:
        # what follows it must start an order by itself, and the route stays
        # where it was written for the dose's own reading (KD-01, 2026-09-28).
        route_first = r"(?:" + ROUTE_BEFORE_THE_DRUG + r"|in)\s+"
        leading_route = re.match(ROUTE_BEFORE_THE_DRUG + r"\s+", body)
        starts = (body, body[leading_route.end():]) if leading_route else (body,)
        medication_start = any(re.match(r"(?:" + pattern + r")\b", start) for start in starts
                               for agents in _AGENTS.values() for pattern in agents.values())
        quantity_start = bool(re.match(r"-?\d+(?:\.\d+)?\s*(?:mcg|ug|mg|g|ml|cc|l|units?|unidades?)\b", body))
        # A disposition written without a verb is still a disposition. "Alta con
        # analgesia oral y control en 7 dias" produced no action and no question
        # at all -- the closing decision of the encounter, lost in silence
        # (2026-09-23).
        # "Nueva vía venosa", "2 VVP gruesas": a new line as written on a chart.
        # Only forms that ask for one: "vía venosa permeable" describes the line
        # the patient has, and whether "reviso la vía" is an examination is a
        # faculty decision (docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md, DC2).
        if _VERBLESS_LINE.fullmatch(body):
            return [{"type": "vascular_access", "operation": "start"}], None
        # Written alone, the endoscopy is asked for only with its urgency: "EDA por várices hace 1 año",
        # "PMH: EGD for banding last year" and "EDA por gastro: ligadura de várices" are what was
        # done, and each called gastroenterology (post hoc, adversarial review of cycle 8).
        if (not someone_elses and _ENDOSCOPY_REQUEST.fullmatch(body) and _ENDOSCOPY_URGENCY.search(body)
                and not _ENDOSCOPY_DONE.search(body)):
            return [{"type": "consult", "service": "gastroenterology"}], None
        consult_start = not someone_elses and bool(_CONSULT_NOUN.match(body))
        # "Bolo de dextrosa 25 g EV" and "bolo de SF 500 mL" are orders as written
        # on a chart; they were quoted back as unreadable (hypoglycaemia reader
        # checks, 2026-09-26).
        bolus_start = bool(re.match(r"(?:bolo|bolus)\s+(?:de\s+|of\s+)?\S", body))
        # "2 ampollas de glucosado al 30%": a count of ampoules starts an order too;
        # without a volume the engine asks for the dose instead of the order being
        # dropped in silence (2026-09-26).
        ampoule_start = bool(re.match(r"(?:\d+|una|dos|tres|one|two|three)\s+(?:ampollas?|amps?|ampoules?)\b", body))
        # The side is said before the procedure ("left chest tube now") and the
        # therapy before its drug ("trombolisis con alteplasa 100 mg"). Both
        # were read as nothing, so the order after a reason and a colon was
        # still lost once the colon was read (DF-22, C02, 2026-09-28).
        side_first = r"(?:left|right|bilateral|izquierd[oa]|derech[oa])\s+"
        therapy_start = bool(re.match(
            r"(?:thromboly\w*|trombol\w*|fibrinol\w*|anticoagula\w*|analgesi\w*|sedaci[oó]n|sedation|"
            r"antibiotic\w*|antibi[oó]tic\w*|profilaxis|prophylaxis)\s+(?:con|with)\s+(?:"
            + "|".join(pattern for agents in _AGENTS.values() for pattern in agents.values()) + r")\b", body))
        # "Sedation with etomidate 8 mg IV before synchronized cardioversion":
        # read as a start, only the procedure ran and the sedation was lost
        # without a word; it is quoted back as before (adversarial review of
        # cycle 6).
        if therapy_start and re.search(
                r"\b(?:cardiover\w*|chest\s+tube|tubo\s+pleural|pleurostom\w*|thoracost\w*|toracost\w*|"
                r"intubat\w*|intubac\w*|intubar|rsi|isr|pacing|marcapaso\w*|procedure|procedimiento|"
                r"reducci[oó]n|reduction|sutur\w*|drenaje|drain\w*)\b", body):
            therapy_start = False
        # Transcutaneous pacing written as a chart line, with its settings:
        # "marcapaso transcutaneo a 70 lpm con 60 mA" was read as nothing, so the
        # alternative after "si no responde" was never a plan (DF-22, C01).
        # Red cells as a chart line: "2 U GR O negativo", "O negativo 2 unidades",
        # "GR 2 U", "2 UGR" (TD-26). "Blood pressure 80/50" or "sangre en las
        # deposiciones" names no count and nothing that qualifies blood, and
        # stays what it is.
        blood_start = not someone_elses and red_cell_line(body) in {"order", "ask"}
        pacing_start = bool(re.match(r"(?:" + _PACING + r")", body)
                            and re.search(r"\d\s*(?:ma|miliamp\w*|milliamp\w*|lpm|bpm|(?:latidos?\s*)?(?:por|/)\s*min)\b",
                                          body))
        # "Epi" is adrenaline on a chart line when a route, a dose or a strength follows it: "Epi
        # 1:1000 IM stat" and "Epi IM stat" were lost without a word (TD-31, cycle 8).
        # So is "epi" after its route ("IM epi stat"), a dose of any size ("epi 300 mcg IM x1")
        # and "epi gtt" (post hoc, blind set of cycle 8).
        # Only with a dose that has its unit or its route: "Epi 8/10 pain" is epigastric pain and
        # "EPI 1ria" a diagnosis. Never someone else's or an earlier dose: "Epi 0.5 mg IM given by
        # EMS", "Epi 0.3 mg IM 20 min ago", "Epi IM at school" gave the drug again (post hoc,
        # adversarial review of cycle 8).
        epi_start = not someone_elses and not _AN_EARLIER_DOSE.search(body) and (any(re.match(
            r"epi\s+(?:(?:im|sc|iv|ev|io|intramuscular\w*|subcut\w*|drip|gtt|goteo|bic|infusion|infusi[oó]n|push)\b|"
            r"(?:\d+(?:[.,]\d+)?|[.,]\d+)\s*(?:mg|mcg|ug|µg|ml|cc)\b|1\s*:\s*10{3,4}\b|"
            r"(?:\d+(?:[.,]\d+)?|[.,]\d+)\s+(?:im|iv|ev|sc|io)\b)", start) for start in starts) or bool(
            leading_route and re.match(r"epi\b", body[leading_route.end():])))
        if not (re.match(shorthand + r"\b", body) or medication_start or quantity_start or bolus_start
                or ampoule_start or therapy_start or pacing_start or blood_start or consult_start or epi_start
                or re.match(side_first + shorthand + r"\b", body)
                or re.match(route_first + shorthand + r"\b", body)
                or re.match(r"(?:alta|discharge|hospitaliza|ingresa|traslada|admit|transfer)", body)):
            return [], None
        if re.search(r"\b(?:was|were|has been|had been|previously|already|caused|improved|worsened|fue|recibio|previamente|ya recibio|mejoro|empeoro)\b", body):
            return [], None

    medication_count = sum(bool(re.search(r"\b(?:" + pattern + r")\b", body)) for agents in _AGENTS.values() for pattern in agents.values())
    has_fluid = bool(re.search(r"\b(?:saline|ns|sf|ringer|ringers|lr|crystalloid|cristaloides?|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica)\b", body))
    if medication_count > 1 or (medication_count and has_fluid):
        return [_clarification("Separate each medication or fluid with its own dose and route so the order is unambiguous.")], verb

    # "Activate the cath lab, aspirin 325 mg and ticagrelor 180 mg PO": the
    # activation was lent to the medicines after it, and each became a consult
    # with no service -- the antiplatelets of a STEMI lost without a word, since
    # before cycle 6; DF-22 (C02, C06) put it in front of more sentences
    # (adversarial comparison with cycle 5, 2026-09-28). A medicine is never a
    # service to activate.
    # "Interconsulta", "referral" and "IC a ..." are consults written as nouns (TD-30, cycle 8). After
    # a discharge they are the plan the patient goes home with: "Discharge home with allergy
    # referral" and "Alta con interconsulta a inmunología" held the discharge asking which
    # specialist (post hoc, adversarial review of cycle 8).
    consult_noun = re.search(r"\b(?:interconsulta|referral)\b|\bic\s+(?:(?:a|al|con)\s+(?:(?:la|el)\s+)?)?(?:"
                             + _SERVICE_NAMES + r")\b", text)
    if (re.search(r"\b(?:consult|call|consultar|interconsultar|llamar)\b", text)
            or (consult_noun and not re.search(r"\b(?:discharge\w*|alta|d/?c|home|domicilio|casa)\b",
                                               text[:consult_noun.start()]))
            or re.search(_SERVICE_PROCEDURE, body)
            or (verb in {"activate", "activar"} and not medication_count and not has_fluid)):
        # A consult that has already happened is not one asked for now: "la interconsulta a
        # cirugía ya fue respondida" was a consult to nobody, asked which specialist, and
        # with the service now read it would have run (TD-30, cycle 8). Only where no order verb
        # asks for it: "Consult urology for decompression since she is already septic" and "Llamar
        # nuevamente a cirugía que ya lo vio" are consults (post hoc, adversarial review of cycle 8).
        # "La interconsulta" reads as the imperative "interconsulta", so the consult said to be
        # answered, done or seen is no request whatever verb was read.
        if re.search(r"\bfue\s+(?:respondid|realizad|hech|vist|evaluad|solicitad|pedid)\w*|\brespondid[oa]s?\b|"
                     r"\b(?:was|were|has\s+been|had\s+been)\s+(?:seen|called|consulted|answered|done|requested|"
                     r"placed)\b", text) or (not verb and re.search(
                         r"\b(?:already|previously|ya\s+(?:fue|lo|la|le|se|vio|evaluo|respondio|vino|paso)|"
                         r"saw\s+(?:him|her|the\s+patient))\b", text)):
            return [], None
        if not verb and (_CONSULT_STATUS.search(text) or re.match(r"(?:" + _NON_CLINICAL_SERVICE + r")\s+consult", text)):
            return [], None
        service = None
        # A surgical subspecialty is not general surgery: "vascular surgery consult" is asked
        # which specialist, as before, rather than sent to general surgery (TD-30, cycle 8).
        subspecialty = re.search(
            r"\b(?:vascular|vasc|thoracic|cardiac|cardiothoracic|plastic|pediatric|paediatric|orthop\w*|maxillo\w*|hand|"
            r"transplant|bariatric|colorectal|hepatobiliary)\s+surg\w*|\bneurosurg\w*|\bneurocirug\w*|"
            r"\bcx\s+(?:vascular|cardio\w*|toracica|plastica|infantil|pediatrica)|"
            r"\bcirug[ií]a\s+(?:vascular|card\w*|tor[aá]cica|pl[aá]stica|pedi[aá]trica|infantil|maxilo\w*|"
            r"ortop\w*|traumatol\w*|de\s+mano|de\s+t[oó]rax)", body)
        # The pulmonary embolism response team is asked for by its name here,
        # and the case declares involving it as what D3 turns on; only the
        # English acronym was listed (2026-09-23).
        for name, pattern in (("PERT", r"\bpert\b|equipo (?:de |para )?(?:respuesta )?"
                                       r"(?:de |a )?(?:tromboembolismo|tep|embolia pulmonar)"),
                              ("cardiology", r"cardiolog|\bcardio\b|\bcards\b"),
                              # The STEMI code is how the cath lab is called here
                              # ("activo codigo infarto"; DF-22, C06).
                              ("cath lab", r"cath(?:eterization)? lab|hemodinamia|hemodinamica|"
                                           r"codigo\s+(?:infarto|iam|scacest|stemi)|stemi\s+(?:code|alert)|code\s+stemi"),
                              # "GI consult", "gastro", an upper endoscopy by its abbreviations
                              # (TD-30, cycle 8); "GI bleed" is not the service.
                              ("gastroenterology", r"gastroenterolog|endoscop|\bgi\s+(?:consult\w*|team|service|"
                                                   r"on[- ]call|fellow)|\bgastro\b|\beda\b|\bveda\b|\begd\b|"
                                                   r"\bogd\b|gastroscop"),
                              # The service that decompresses an obstructed,
                              # infected kidney, asked for by its name or by what
                              # it is being asked to do (2026-09-23).
                              ("urology", r"urolog|\buro\b|nefrostom[ií]a|nephrostomy|"
                                          r"cat[eé]ter\s+doble\s+j|doble\s+j|double[- ]j|"
                                          r"ureteral\s+stent|stent\s+ureteral|"
                                          r"desobstru|descompresi[oó]n\s+(?:de\s+la\s+)?v[ií]a\s+urinaria"),
                              # "Surgery consult", "interconsulta a cirugía": general surgery by
                              # its plain name too (TD-30, cycle 8); a subspecialty stays asked.
                              ("surgery", r"cirug[ií]a general|general surgery|cirujano" + (
                                  "" if subspecialty else r"|(?<![\w-])(?:trauma\s+)?surgery\b|\bsurgical\s+"
                                                          r"(?:team|service|consult\w*)|\bcirug[ií]a\b|"
                                                          r"\bgen(?:eral)?\.?\s+surg\b|"
                                                          # "Blood cx" are cultures (post hoc, adversarial
                                                          # review of cycle 8).
                                                          r"(?<!blood\s)(?<!urine\s)(?<!sputum\s)(?<!wound\s)\bcx\b")),
                              # Named and asked "which specialist?" all the same
                              # (hypoglycaemia reader checks, 2026-09-26).
                              ("endocrinology", r"endocrinolog|diabetolog"),
                              ("nephrology", r"nefrolog|nephrolog"),
                              ("neurology", r"neurolog"),
                              ("internal medicine", r"medicina\s+interna|internal\s+medicine|internista"),
                              ("toxicology", r"toxicolog|poison\s+control"),
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
        return [{"type": "disposition", "destination": destination}, *_attached_treatment(body)], verb
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
    # "Dextrosa al 10%" and "SG 10%" are the infusion too (2026-09-25): until
    # then "inicio infusion de dextrosa al 10% a 100 ml/h" was read as a 10 g
    # bolus, 10% of 100 mL.
    if re.search(r"\b(?:d10|d\s*10|dextrose\s*10|dextros[ae]\s*(?:al\s*)?10|glucosa(?:do)?\s*(?:al\s*)?10|"
                 r"suero\s+glucosado|sg\s*(?:al\s*)?10|solucion\s+glucosada\s*(?:al\s*)?10)\b", body):
        rate = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:ml|cc)\s*(?:/|\s+(?:per|por|cada)\s+)\s*(?:h|hr|hour|hora)\b", body)
        return [{"type": "dextrose_infusion", "rate_ml_h": float(rate[1]) if rate else None,
                 "concentration_percent": 10, "operation": _operation(verb)}], verb or "start"
    if re.search(r"\b(?:oral\s+(?:glucose|carbohydrate|sugar)|glucose\s+gel|juice|zumo|jugo|"
                 r"carbohidrato\s+oral|glucosa\s+oral|az[uú]car\s+oral|comida|colaci[oó]n|"
                 r"(?:oral\s+)?snack|something\s+to\s+eat)\b", body):
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
        if re.search(r"\b(?:already|ya\s+(?:esta\s+)?(?:instalad|puest|colocad)\w*|in\s+place|en\s+su\s+lugar|"
                     r"(?:placed|inserted|instalad[oa]|colocad[oa])\s+(?:by|at|earlier|por|antes))\b", body):
            # "Chest tube already in", "tubo pleural ya instalado": what is there,
            # never a tube placed now (post hoc, blind set of cycle 7).
            return [], None
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
        per_kilo_im = None if rate_match else _PER_KILO_ANY.search(body)
        if kind == "epinephrine" and per_kilo_im and intramuscular:
            # "0.01 mg/kg IM": a dose per kilogram of the intramuscular route.
            # Until 2026-09-26 the bare number fell through to the infusion
            # reader, which asked for infusion units; nothing wrong ran, but
            # the order was misread. The weight turns it into milligrams and
            # the validation range then judges the resulting dose openly.
            order = _per_kilo_order("epinephrine_im", None, per_kilo_im, body)
            order.pop("agent", None)
            order["route"] = ("SC" if re.search(r"\b(?:sc|subcutaneous(?:ly)?|subcut[aá]ne[ao])\b", body)
                              else "IM")
            return [order], verb or "give"
        # An intramuscular adrenaline written without a dose, or with only its strength
        # ("1:1000", "1 mg/mL"), is the intramuscular order still to be dosed: the engine asks
        # its dose in milligrams. It was read as an infusion and asked a rate in mcg/min
        # (TD-31, cycle 8).
        if (kind == "epinephrine" and intramuscular and not rate_match and not mass_dose and not per_kilo_im
                and not re.search(r"\b(?:drip|gtt|infusion|infusi[oó]n|bic|goteo|perfusion|perfusi[oó]n|continuous|"
                                  r"continu[ao])\b", body)):
            route = "SC" if re.search(r"\b(?:sc|subcutaneous(?:ly)?|subcut[aá]ne[ao])\b", body) else "IM"
            return [{"type": "epinephrine_im", "dose_mg": None, "route": route}], verb
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
        infusion_order = {"type": kind, "rate": rate, "units": units, "operation": _operation(verb)}
        if units == "mcg/kg/min" and _weight_basis(body):
            infusion_order["weight_basis"] = _weight_basis(body)
        return [infusion_order], verb
    if re.search(_OXYGEN_MENTION, body):
        return [_oxygen_order(body, verb)], verb
    # "Blood products" and "hemoderivados" name no product: which one, and how
    # many units, is asked, never answered with red cells (TD-26, D).
    if _GENERIC_BLOOD_PRODUCTS.search(body) and not unmodelled_blood_product(body, verb):
        return [_clarification("Specify which blood product to give and how many units.")], verb
    if re.search(r"\b(?:saline|normal saline|ns|sf|sf|ringer|lactated ringers?|lr|crystalloid|cristaloides?|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica|sueros?|fluid|fluids|volumen)\b", body):
        if _operation(verb) == "stop":
            # "Stop the normal saline" ends a running infusion; it is not a new bolus.
            fluid_type = ("normal saline" if re.search(r"\b(?:saline|ns|sf|salino|fisiologico|fisiologica)\b", body)
                          else "lactated Ringer's" if re.search(r"\b(?:ringer|ringers|lr)\b", body) else None)
            return [{"type": "fluid", "operation": "stop", "fluid_type": fluid_type}], verb
        # "SF 1000 ml ev a 125 ml/h": the rate is the resident's, read and kept
        # as declared; it used to hide the volume, and the order was held
        # asking for one (faculty decision 5, 2026-09-25).
        per_hour = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ml|cc)\s*(?:/|\s+(?:por|per|a\s+la|an?)\s+)\s*(?:h|hr|hora|hour)\b",
                             body)
        # "SF 30 ml/kg": a volume per kilogram, turned into mL on the patient's
        # weight by weight_based_doses. It used to be read as 30 mL (2026-09-27).
        per_kilo = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ml|cc)\s*(?:/|\s+(?:por|per)\s+)\s*(?:kg|kilo|kilogramo|kilogram)s?\b"
                             r"(?!\s*/)", body)
        if per_kilo and not per_hour:
            fluid_type = ("normal saline" if re.search(r"\b(?:saline|ns|sf|salino|(?:suero\s+)?fisiologic[oa]|solucion fisiologica)\b", body)
                          else "lactated Ringer's" if re.search(r"\b(?:ringer|ringers|lr)\b", body)
                          else "crystalloid" if re.search(r"\b(?:crystalloid|cristaloides?)\b", body) else None)
            fluid = {"type": "fluid", "volume_ml_per_kg": float(per_kilo.group(1).replace(",", ".")),
                     "volume_ml": None, "fluid_type": fluid_type}
            if _weight_basis(body):
                fluid["weight_basis"] = _weight_basis(body)
            route = _route(body)
            if route:
                fluid["route"] = route
            return [fluid], verb
        measured = body if not per_hour else body[:per_hour.start()] + " " + body[per_hour.end():]
        volume, units = _amount(measured, r"ml|cc|lts?|liters?|litres?|litros?|l")
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
        if per_hour and volume:
            rate = float(per_hour.group(1).replace(",", "."))
            if rate > 0:
                fluid.update(rate_ml_h=rate, administration_duration_min=round(volume / rate * 60, 1))
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
        # A bare drug name is only an order with an explicit command or dose. A
        # glucose written as its solution ("D50 50 mL IV", "dextrosa al 50% 50 mL")
        # carries its dose; until 2026-09-25 it was dropped without a word.
        # "Glucosa 40 mg/dL" is a result, and a concentration is never a dose: it
        # gave 40 mg of dextrose (adversarial review of cycle 7; as before).
        if (verb or re.search(r"\d\s*(?:mcg|ug|mg|g|units?|ui)\b(?!\s*/\s*(?:dl|l)\b)", body)
                or (kind == "dextrose" and (_dextrose_from_solution(body)
                                            or re.search(r"\bampollas?\b|\bamps?\b|\d\s*%", body)))):
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
    dose_piece = re.sub(r"\b(?:over|durante|en)\s+\d+(?:\.\d+)?\s*(?:minutes?|mins?|minutos?|hours?|horas?|hrs?|h|seconds?|"
                        r"segundos?)\b", "", piece)
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
    # "En 2 h", "over 2 hrs": the hour written short (post hoc, blind set of cycle 8); it was
    # dropped, and "2 U GR en 2 h" was asked whether to transfuse at all.
    matches = list(re.finditer(r"\b(?:over|durante|en)\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|minutos?|hours?|horas?|hrs?|h|"
                               r"seconds?|segundos?)\b", text))
    # When the patient is checked again is not how long the treatment runs: "Furosemida 40 mg ev
    # con control de diuresis en 2 h" ran the furosemide over 2 hours, and "Noradrenalina 0,1
    # mcg/kg/min ev con control de PAM en 1 h" was held (post hoc, adversarial review of cycle 8;
    # "en 1 hora" was read so before the cycle).
    matches = [match for match in matches if not re.search(
        r"\b(?:control(?:es|ar)?|controlando|chequear|check|recheck|monitor\w*|vigilar|reevaluar|reassess\w*|medir|"
        r"evaluar|evaluate|revisar|seguimiento|follow[- ]?up|f/u)\b[^,;]*$", text[:match.start()])]
    # A disposition or a consult has no delivery time: "de alta con control en 24
    # horas" states when the patient is seen again, not how long an order runs.
    treatments = [a for a in actions if a['type'] not in {'diagnostic', 'reassessment', 'clarification',
                                                          'disposition', 'consult', 'reperfusion_referral'}]
    if matches and treatments:
        if len(matches) != 1 or len(treatments) != 1:
            return [_clarification("Specify one delivery duration for each treatment.")], verb
        value, unit = float(matches[0][1]), matches[0][2]
        value *= 60 if unit.startswith(('hour', 'hora', 'hr')) or unit == 'h' else 1 / 60 if unit.startswith(('second', 'segundo')) else 1
        # "2 U GR en 2 horas c/u", "2 U PRBC over 2 h each": the time of each unit, so the
        # units run one after another; they ran in 2 hours in all (TD-32, cycle 8).
        if (treatments[0].get("type") == "blood" and (treatments[0].get("units") or 0) > 1
                and re.match(r"\s*(?:c/u|cada\s+un[ao]|cada\s+unidad|each|per\s+unit|por\s+unidad)\b",
                             text[matches[0].end():])):
            value *= treatments[0]["units"]
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


# A reason or a label written before a colon, and the order after it (DF-22,
# C02, 2026-09-28): "Anaphylaxis with stridor: epinephrine 0.5 mg IM now", "TEP
# de alto riesgo: alteplasa 100 mg ev en 2 horas", "Plan: aspirin 300 mg PO".
# The colon ended nothing, so the order was read as part of the label: it
# vanished, or was held as unreadable, or the repeat after it was kept as a plan
# of nothing, while the page ran whatever else the entry said and the Trace
# showed the resident not doing what they wrote. A colon between two digits is a
# ratio or a time ("1:1000", "10:30").
_LABEL_COLON = re.compile(r"(?<!\d):|:(?!\d)")
# What a colon is never stepped over after, because it makes what follows
# something other than an order now: a condition ("si no responde:", "PRN:",
# "SOS:"), a time ("a los 5 minutos:", "una vez estable:", "later:",
# "post-intubation:"), an alternative ("plan B:", "alternativa:"), something
# awaited ("pendiente:"), a withholding ("evitar:", "contraindicado:"), or a list
# of what the patient takes or is allergic to ("medicamentos:", "alergias:").
# What follows such a head is read as it was before the colon was stepped over:
# held or kept as a plan, never run now on a guess (DF-22, §8).
_COLON_KEEPS = re.compile(
    r"\b(?:if|si|unless|salvo\s+que|a\s+menos\s+que|en\s+caso\s+de|when|whenever|cuando|"
    r"once|una\s+vez|later|luego|then|next|afterwards?|subsequently|eventual\w*|tomorrow|overnight|"
    r"despues|mas\s+tarde|posteriormente|posterior\s+(?:a|al)|siguiente|proxim[oa]|manana|until|hasta|"
    r"after|tras|before|antes|previo|pre|post|pos|"
    r"prn|sos|as\s+needed|if\s+needed|segun\s+necesidad|de\s+ser\s+necesario|"
    r"rescue|rescate|backup|back-up|fallback|plan\s+b|alternativ\w*|alternate|second[-\s]+line|"
    r"segunda\s+linea|tercera\s+linea|"
    r"pending|pendientes?|awaiting|waiting|en\s+espera|esperando|"
    r"avoid|evitar|evito|contraindicad\w*|contraindicat\w*|"
    r"medicamentos?|medications?|meds|farmacos|remedios|tratamiento\s+habitual|home|usual|habituales?|"
    r"alta|discharge|egreso|domicilio|"
    r"antecedentes?|history|historia|pmh|alergi\w*|allerg\w*|alergic\w*|"
    # What the ambulance did, or what has gone in so far: "SAMU: 1 U GR O
    # negativo en ruta", "Balance: 2 U GR, 2 L SF" (adversarial review of cycle 7).
    r"samu|ems|prehospital\w*|pre-?hospital\w*|en\s+ruta|en\s+route|ambulancia|ambulance|traslado|"
    r"balance|ingresos|egresos|intake|output|total|so\s+far|hasta\s+ahora)\b"
    r"|\b(?:post|pos|pre)[-\s]?(?:intubac\w*|intubat\w*|op\w*|procedim\w*|procedur\w*|sedac\w*|sedat\w*|"
    r"reperfus\w*|pci|icp|parto|partum|cardiover\w*|rsi|isr|alta|discharge|transfus\w*|trasfus\w*|tac|ct)\b"
    r"|\b(?:a\s+los|at|after|tras|en|in|dentro\s+de|despues\s+de|cada|every)\s+\d"
    # A threshold ("sobre 150", "above 65", "< 90") or a state to be reached
    # ("con HGT estables", "with a stable MAP") makes the head a condition:
    # "Con HGT estables sobre 150: suspender SG 10%" ran the change at once
    # (found by the second blind held-out check, 2026-09-28). So does a result
    # that may not be in yet: "Con angioTAC positivo: enoxaparina 1 mg/kg" read
    # the anticoagulation as ordered now (third blind check, 2026-09-28). "With
    # a positive CTA" can also be the reason for an order now; kept, the head is
    # quoted back and asked about, as before the colon was read.
    r"|(?:\b(?:sobre|bajo|encima\s+de|debajo\s+de|mayor(?:es)?\s+(?:a|de|que)|menor(?:es)?\s+(?:a|de|que)|"
    r"above|below|over|under|greater\s+than|less\s+than|more\s+than|at\s+least|al\s+menos)|[<>≤≥]=?)\s*\d"
    r"|\b(?:con|with|when|cuando)\b[^:]*\b(?:estables?|stable|estabilizad\w*|stabili[sz]ed|normalizad\w*|"
    r"normali[sz]ed|controlad\w*|controlled|resuelt\w*|resolved|"
    r"positiv[oa]s?|positive|negativ[oa]s?|negative|confirmad[oa]s?|confirmed)\b")
# A change in the patient, or a hedge, is a contingency only when it is the
# whole head: "Persiste:", "Refractory:", "No response:", "Consider:". With the
# finding it describes it is the reason for an order now: "Hipotension
# persistente:", "Refractory hypotension:", "Worsening hypoxemia:", "Failed
# intubation:", "Considerar anafilaxia:".
_CONTINGENCY_ALONE = re.compile(
    r"\b(?:persist\w*|refractor\w*|refractari\w*|wors\w*|peor|empeor\w*|deterior\w*|fail\w*|falla\w*|fallo|"
    r"fallid\w*|fracas\w*|recurr\w*|recidiv\w*|no\s+respon\w*|not\s+respon\w*|non-?response|"
    r"without\s+response|sin\s+respuesta|no\s+response|does\s*n[o']?t\s+respond\w*|"
    r"consider\w*|maybe|perhaps|quizas?|tal\s+vez|posiblemente|possibly|ideal(?:ly|mente)|opcional\w*|optional\w*)\b")
_HEAD_FILLER = re.compile(
    r"\b(?:el|la|los|las|lo|the|a|an|it|he|she|they|ella|ellos|paciente|patient|pt|still|sigue|siguen|aun|"
    r"todavia|is|es|esta|are|y|and|o|or|de|del|al|to|con|with|mas|more|again|nuevamente|otra\s+vez|entonces)\b")
# A head that only withholds: "No:", "No dar:", "Do not give:", "Sin:".
_WITHHOLD_HEAD = re.compile(
    r"(?:no|not|never|nunca|sin|hold|do\s+not|don't)"
    r"(?:\s+(?:dar|give|use|usar|administrar|administer|poner|start|iniciar|indicar))?")


def _label_before_colon(head):
    """Whether what precedes a colon is a reason or a label, not part of an order.

    Only a head that orders nothing by itself -- no action, no plan, not even an
    unreadable order -- is stepped over. "Oxygen: nasal cannula 2 L/min" and
    "Norepinephrine: 0.1 mcg/kg/min" keep reading as the one order they are.
    """
    # A heading that names the goal of what follows it: "Hemorrhage control: surgery
    # consult" lost the consult, since the heading alone asks which measure, and "control"
    # opens "control de hemorragia" as a verb would (TD-30, cycle 8).
    if re.fullmatch(r"(?:h[ae]morrhage|bleeding|hemorragia|sangrado)\s+control|"
                    r"control\s+(?:de\s+(?:la\s+)?hemorragia|del\s+sangrado|de\s+sangrado|of\s+(?:the\s+)?bleeding)", head):
        return True
    if _COLON_KEEPS.search(head) or _WITHHOLD_HEAD.fullmatch(head) or _COMMAND.match(head):
        return False
    if re.fullmatch(r"(?:" + _RED_CELL_NAMES + r"|gre?|(?:o|0)\s*(?:rh\s*)?-?\s*(?:neg|pos)\w*)", head):
        # "GR: 2 U" is the red cells and their count (adversarial review of cycle 7).
        return False
    if _CONTINGENCY_ALONE.search(head) and not _HEAD_FILLER.sub(
            " ", _CONTINGENCY_ALONE.sub(" ", head)).strip(" ,."):
        return False
    heard = parse_family_actions(head)
    return not heard["actions"] and not heard["future_details"]


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


# A dose that was given before, somewhere else or by someone else, or that is a plan: "20 min ago",
# "prior to arrival", "at home", "by mom", "ya administrada", "at 14:05", "q5-15 min PRN" (post hoc,
# adversarial review of cycle 8).
_AN_EARLIER_DOSE = re.compile(
    r"\b(?:ago|hace\s+\d|prior\s+to\s+arrival|pta|at\s+(?:home|school|work)|en\s+(?:la\s+)?casa|en\s+el\s+colegio|"
    r"by\s+(?:his|her|the)?\s*(?:mom|mother|dad|father|wife|husband|family|parents?|school\s+nurse)|administrad[oa]s?|"
    r"dad[oa]s?|given|administered|repeated|repetid[oa]s?|prn|sos|at\s+\d{1,2}[:.]\d{2}|a\s+las\s+\d{1,2}[:.]\d{2}|"
    r"descartad[oa]s?)\b|\bq\s*\d+\s*(?:-\s*\d+\s*)?min")
_WHEN_WORD = re.compile(r"(?:when|whenever|as\s+soon\s+as|cuando|en\s+cuanto|tan\s+pronto\s+como|una\s+vez\s+que|once|"
                        r"apenas)\b")
# A reason that the "when" belongs to: "Give D50 50 mL IV now as he gets confused when his glucose
# drops", "dado que la PA cae cuando se sienta".
_REASON_BEFORE_WHEN = re.compile(
    r"\b(?:as|since|because|given\s+that)\s+(?:he|she|they|it|the\s+patient|pt|his|her|their)\b|"
    r"\b(?:porque|ya\s+que|dado\s+que|debido\s+a\s+que|puesto\s+que)\b|^como\b")


def _describes_what_was_seen(sentence, conditional):
    """Whether a "when" is part of what the resident saw rather than a condition on an order.

    What stands before it in its own clause decides: an order ("transfundir 2 U GR cuando Hb < 7")
    makes it the order's condition; the patient's finding ("mareada cuando la PA baja", "presyncope
    when BP drops") or a reason ("... as he gets confused when his glucose drops") makes it part
    of the description (post hoc, adversarial review of cycle 8).
    """
    if not _WHEN_WORD.match(conditional.group(0)):
        return False
    segment = re.split(r"[,;:]|\s[-–—]\s|->|→|\s+(?:y|e|and|then|luego|so|entonces)\s+",
                       sentence[:conditional.start()])[-1].strip()
    if not segment:
        return False
    if _REASON_BEFORE_WHEN.search(segment):
        return True
    return not (_COMMAND.match(segment) or _REPEAT_START.match(segment) or _names_a_drug(segment)
                or re.match(r"(?:again|another|otra\s+vez|de\s+nuevo|nuevamente)\b", segment) or _orders_now(segment))


def _order_inside(clause):
    """Where an order starts inside a condition written without a comma, or "".

    "cuando la sat baje de 92% repetir", "when hgb drops below 7 transfuse 1 unit PRBC" (post hoc,
    adversarial review of cycle 8).
    """
    for start in re.finditer(r"(?:^|\s|->|→|=>)\s*(?=[a-z])", clause):
        rest = clause[start.end():]
        # "Iban a iniciar dopamina" tells what someone was going to do.
        if re.search(r"\b(?:iba|iban|ibamos|iria|irian|was|were)\s+(?:a|going\s+to)\s*$", clause[:start.end()]):
            continue
        if _COMMAND.match(rest) or _OK_DISCHARGE_TAIL.match(rest) or _REPEAT_START.match(rest):
            return rest
    return ""


def _ringer_abbreviation(text):
    """"RL" is how Ringer lactato is written in Chile ("RL 500 ml ev", "bolo de RL").

    It was read as nothing, or quoted back with a verb (post hoc, blind set of cycle 8). Only
    before a volume, a route or a bolus, or after what gives a fluid, is it the fluid.
    """
    text = re.sub(r"\brl\b(?=\s*(?:\d|ev\b|iv\b|a\s+chorro|en\s+bolo|bolo|tibio|wide\s+open))", "lr", text)
    return re.sub(r"\b(de|pasar|administrar|bolo|bolus|con)\s+rl\b", r"\1 lr", text)


_STUDIES_DONE = None


def _studies_done():
    """Studies joined by "y"/"and" and closed by what has happened to them (post hoc, cycle 8)."""
    global _STUDIES_DONE
    if _STUDIES_DONE is None:
        item = (r"\b(?:" + "|".join(_DIAGNOSTICS.values()) + r"|urocultivos?|urine\s+cultures?|cultivos?|cultures?)\b"
                r"(?:\s*[x×]\s*\d+)?")
        _STUDIES_DONE = re.compile(
            r"(?:^|(?<=[,;:]))\s*" + item + r"(?:\s*(?:\by\b|\band\b|\+|&)\s*" + item + r")*\s+"
            r"(?:(?:ya|already)\s+)?(?:tomad[oa]s?|enviad[oa]s?|drawn|sent|done|realizad[oa]s?|pendientes?|pending|"
            r"en\s+curso|in\s+progress|resulted|listos?|listas?)\b")
    return _STUDIES_DONE


def _state_tail(rest):
    """How much of what follows a study's state still describes it.

    "Hemocultivos x2 ya tomados en el SAPU" ends with the state's own words; "Hemocultivos tomados y
    ceftriaxona 2 g ev", "Blood cultures pending - start ceftriaxone", "Lactate pending so give 30
    mL/kg LR" go on to an order, which is read. The whole rest of the clause went with the state,
    and the antibiotic was lost without a word (post hoc, adversarial review of cycle 8).
    """
    clause = re.match(r"[^,;:]*", rest).group(0)
    # "Before" names when the study was taken ("tomados antes del antibiótico"), unless an order
    # follows it ("drawn prior to ceftriaxone 2 g IV", asked about as before).
    stop = re.search(r"\s[-–—]\s|->|→|\s+(?:y|e|and|then|luego|so|pero|but)\b|"
                     r"\s+(?:prior\s+to|before|antes\s+de(?:l)?)\s+(?=(?:starting\s+|iniciar\s+|dar\s+)?(?:la\s+|el\s+|the\s+)?"
                     r"(?!antibiotics?\b|antibioticos?\b|abx\b|atb\b|tratamiento\b|treatment\b))", clause)
    end = stop.start() if stop else len(clause)
    for start in re.finditer(r"\s+(?=[a-z])", clause[:end]):
        if _COMMAND.match(clause[start.end():]) or _orders_now(clause[start.end():end]):
            return start.start()
    return end


def _chart_with(text):
    """"W/" is "with" in a chart note ("OK to dc home w/ epipen rx"); "w/o" is left alone.

    Unread, the discharge that carried the prescription was lost (post hoc, blind set of cycle 8).
    """
    return re.sub(r"\bw/(?!o\b)\s*", "with ", text)


def _unit_point(text):
    """The point of "U." before the product it counts is an abbreviation, not a full stop.

    "2 U. GR" and "2 U. PRBCs" ended the sentence at the point, and the units lost
    their product: nothing was read, or the count was asked again (TD-32, cycle 8).
    """
    # Only before red cells, and only when the sentence has not named its product before the count:
    # "Transfuse PRBC 2 U. Platelets if count < 50." and "PRBC 2 U. FFP 2 U." are two sentences,
    # and read as one the red cells were not given (post hoc, adversarial review of cycle 8).
    def join(match):
        opening = max(text.rfind(".", 0, match.start()), text.rfind(";", 0, match.start()),
                      text.rfind("\n", 0, match.start())) + 1
        if re.search(r"\b(?:" + _RED_CELL_WORDS + r"|gre?|" + _PRODUCT_NAMES + r"|" + _PRODUCT_WORDS + r")\b",
                     text[opening:match.start()]):
            return match.group(0)
        return match[1] + " u "
    return re.sub(r"\b(\d+)\s*u\.\s*(?=(?:de\s+)?(?:" + _RED_CELL_WORDS + r"|gre?|o\s*(?:rh\s*)?[-+]?\s*(?:neg|pos))\b)",
                  join, text)


# "OK to discharge", "ok para alta": the discharge said as a clearance, in both languages
# (KD-05, cycle 8). Not when it is denied or asked ("not ok for discharge yet", "¿está ok
# para alta?"), and not "labs OK".
_OK_TO_DISCHARGE = re.compile(
    r"(?P<lead>^|(?<=[.;\n,])\s*)(?:(?:the\s+)?(?:pt|patient|he|she|el\s+paciente|la\s+paciente|paciente)"
    r"(?:\s+is\s+|'s\s+|\s+esta\s+|\s+))?(?:ok(?:ay)?|okey)\s+(?:(?:to|for|para)\s+)?"
    r"(?P<what>(?:be\s+)?discharged?(?:\s+home)?|d/?c(?:\s+home)?|go\s+home|(?:dar(?:le|la|lo)?\s+de\s+)?alta"
    # "Ok para alta dosis de salbutamol" is a high dose (post hoc, adversarial review of cycle 8).
    r"(?!\s+(?:dosis|flujo|frecuencia|concentracion|presion|intensidad|prioridad|sospecha|probabilidad)\b)"
    r"(?:\s+a\s+(?:domicilio|(?:la\s+)?casa))?|irse\s+(?:a\s+(?:la\s+)?casa|de\s+alta)|egreso|"
    # "Ok para la casa" (post hoc, blind set of cycle 8).
    r"(?:ir\s+)?(?:a\s+)?(?:la\s+)?casa|domicilio)\b")


# What makes a clearance something other than a discharge now (post hoc, adversarial review of
# cycle 8). "OK to d/c IV fluids" stops the fluids: "d/c" is a discharge only with nothing after
# it but the patient's plan. A time or a condition puts it off ("OK to dc home after 4 h
# observation", "ok para alta mañana"), a "no" after it denies it ("OK to discharge: no"), and
# another service's clearance is theirs ("Per surgery, OK to discharge", "OK to discharge from
# ortho standpoint"). Each of these was a discharge now, the trigger of two critical events.
_DC_OBJECT_ALLOWED = re.compile(r"\s*(?:$|[.,;!]|(?:with|con|and|y|home|to\s+home|f/u|follow)\b)")
_CLEARANCE_PUT_OFF = re.compile(
    r"\b(?:after|once|when|whenever|until|tomorrow|tonight|later|in\s+the\s+(?:am|morning)|am|pending|if|unless|"
    r"tras|despues|luego\s+de|una\s+vez|cuando|en\s+cuanto|hasta|manana|mas\s+tarde|pendiente|si|salvo)\b")
_CLEARANCE_DENIED = re.compile(r"\s*(?:[:\-–—]\s*)?(?:no|not|nope|todavia\s+no|aun\s+no|not\s+yet)\b|\s*,?\s*(?:but|pero)\b")
_SOMEONE_ELSES_CLEARANCE = re.compile(
    r"\b(?:per|according\s+to|segun|por\s+parte\s+de)\s+(?!(?:protocol|protocolo)\b)[a-z]|"
    r"\b(?:standpoint|perspective|point\s+of\s+view|punto\s+de\s+vista)\b")


def _ok_to_discharge(text):
    def say(match):
        sentence = text[match.start():].split(".")[0]
        if "?" in sentence or "¿" in text[max(0, match.start() - 2):match.end()]:
            return match.group(0)
        start = max(text.rfind(".", 0, match.start()), text.rfind(";", 0, match.start()),
                    text.rfind("\n", 0, match.start())) + 1
        ends = [i for i in (text.find(".", match.end()), text.find(";", match.end()), text.find("\n", match.end()))
                if i >= 0]
        whole = text[start:min(ends) if ends else len(text)]
        tail = text[match.end():min(ends) if ends else len(text)]
        clause_tail = re.split(r"[,;:]|\s[-–—]\s", tail)[0]
        if match["what"].startswith("d") and "home" not in match["what"] and not _DC_OBJECT_ALLOWED.match(tail):
            return match.group(0)
        if _CLEARANCE_DENIED.match(tail) or _SOMEONE_ELSES_CLEARANCE.search(whole):
            return match.group(0)
        # A condition on the patient's course is read as the discharge's condition, a plan
        # ("OK for d/c home once afebrile"); any other time puts the clearance off.
        if _CLEARANCE_PUT_OFF.search(clause_tail) and not re.match(r"\s*\b" + _WHEN_CONDITION, clause_tail):
            return match.group(0)
        spanish = bool(re.search(r"alta|casa|irse|egreso|domicilio", match["what"]))
        home = bool(re.search(r"home|casa|domicilio", match["what"])) or match["what"].startswith(("go", "irse", "ir "))
        return match["lead"] + ("alta" + (" a domicilio" if home else "") if spanish
                                else "discharge" + (" home" if home else ""))
    return _OK_TO_DISCHARGE.sub(say, text)


def parse_family_actions(text) -> dict:
    """Return source-ordered action dictionaries without changing patient state.

    Semicolons, full stops, and newlines end conditional/negated scope. Commas,
    ``and``/``y`` and ``+`` can chain orders and inherit an explicit order verb.
    A conditional instruction is retained as a future plan, never executed now.
    """
    raw = str(text or "")
    # A run of spaces or tabs means one space; a run of thousands took seconds to read, since
    # several steps scan the text again at every position (TD-27, cycle 8). Line breaks still
    # end a sentence.
    spaced = re.sub(r"[ \t\u00a0]{2,}", " ", raw)
    normalized = _spanish_imperatives(
        _spanish_proclitics(_reason_then_order(_declared_intention(_opening_time_word(
            _fluid_stop_verbs(_through_the_line(_correcting_with(_ok_to_discharge(_unit_point(_chart_with(
                _ringer_abbreviation(_normalize(spaced)))))))))))))
    # A resident who says to wait for a result before treating has said
    # something about sequence that the engine must not optimise away (faculty
    # specification 2026-09-23, section 5). The two halves are parsed
    # separately and the second half is marked as waiting on the first.
    held_until, normalized = _sequenced(normalized)
    actions, future, details = [], [], []

    def keep(text, kind, **structure):
        # What is recognised and not executed now, and why: a medicine the
        # simulator does not model, a prescription for home, a conditional plan,
        # a repeat instruction with its interval, count and condition (DF-16b),
        # or advice to the patient (faculty decision 3, 2026-09-25).
        future.append(text)
        details.append({"text": text, "kind": kind, **structure,
                        **(unmodelled_detail(text) if kind == "not_modelled" else {})})
        if kind == "not_modelled" and details[-1].get("prescription"):
            details[-1]["kind"] = "prescription"

    # Advice that closes a sentence is recorded after what the sentence says
    # before it, so the plan keeps the resident's order: "discharge with
    # cardiology follow-up and return if the palpitations come back" is the
    # follow-up, then the return advice (DF-10, 2026-09-27). A repeat that
    # closes a sentence follows the order it repeats the same way (DF-16b).
    trailing_advice = []

    def flush_trailing_advice():
        while trailing_advice:
            item = trailing_advice.pop(0)
            text, kind, structure = item if isinstance(item, tuple) else (item, "advice", {})
            keep(text, kind, **structure)
    # The last sentence that ordered something: what a repeat written on its
    # own after it ("salbutamol 5 mg nbz; repetir cada 20 min") repeats.
    last_order = None
    # Where the massive transfusion protocol's activation was recorded: its cooler,
    # asked for after it, belongs to that record (A–J of cycle 7).
    protocol_kept = None
    # A question ends its sentence: "Is she pregnant? Check a urine pregnancy
    # test" was read as one question, and the test was lost (adversarial review).
    queue = re.split(r"[;\n]+|(?<=\?)\s+|(?<!\d)\.(?!\d)|(?<=\d)\.(?!\d)", normalized)
    # Several sentences are a list too: "Monitor; vía venosa; oxígeno…".
    several_sentences = sum(1 for sentence in queue if sentence.strip()) > 1
    while queue:
        flush_trailing_advice()
        sentence = queue.pop(0).strip()
        if not sentence:
            continue
        if sentence.endswith("?") and (_A_QUESTION_TO_THE_PATIENT.match(sentence) or sentence.startswith("\u00bf")
                                       or re.match(r"(?:is|are|was|were|should|would|could|will|do|does|did|vale|sera|"
                                                   r"seria|debo|deberia|deberiamos|podemos|puedo|hay\s+que)\b",
                                                   sentence)):
            # "Do you have any pain?": asked of the patient, and never an order,
            # now that a question ends its sentence.
            continue
        # "Dx: order" -- the label or reason is the resident's reasoning, which
        # the reasoning capture reads; the order after the colon is a clause of
        # its own (DF-22, C02).
        colon = _LABEL_COLON.search(sentence)
        if colon:
            head, rest = sentence[:colon.start()].strip(" ,"), sentence[colon.end():].strip(" ,")
            if head and rest and _label_before_colon(head):
                queue.insert(0, rest)
                continue
        # A balance of what the patient received orders nothing: "Balance: 2 U GR,
        # 2 L SF" and "Ingresos: 2 U GR y 1 L de SF" ran the saline again (post hoc,
        # cycle 7; the red cells were already read as history). An order verb in
        # it is still read: "So far no response, give 1 L NS".
        summary = re.match(r"(?:balance(?:\s+hidrico)?|ingresos|egresos|intake|output|so\s+far|hasta\s+ahora|"
                           r"acumulado)\b\s*[:,-]?\s*", sentence)
        if summary and not any(_COMMAND.match(part.strip())
                               for part in re.split(r",|;|\b(?:y|and|then|luego)\b", sentence[summary.end():])):
            continue
        # "Hemocultivos x2 y urocultivo ya tomados", "blood cultures and lactate already
        # drawn": the state closes every study joined before it, and none is asked for again
        # (post hoc, blind set of cycle 8; without the count it was so before the cycle).
        done = _studies_done().search(sentence)
        if done:
            after = done.end() + _state_tail(sentence[done.end():])
            rest = re.sub(r"^(?:[\s,:\-–—>]|(?:y|e|and|then|luego|so|pero|but)\b)+", "", sentence[after:])
            sentence = (sentence[:done.start()] + " " + rest).strip(" ,")
            if not sentence:
                continue
        # Two blood products given one ratio or one shared count: "GR y plasma 1:1,
        # 4 U de cada uno" and "Plasma y GR 1:1" were lost without a word, and
        # "PRBC and FFP 1:1, 4 units each" half read (post hoc, cycle 7). Which
        # count belongs to which product is the resident's to say (TD-26, D), as for
        # "GR/PFC 2 U c/u". What happened, a plan, the protocol's activation and
        # someone else's account are read as before.
        if (_SHARED_BLOOD_COUNT.search(sentence) and re.search(r"\b(?:" + _RED_CELL_WORDS + r"|gre?)\b", sentence)
                and re.search(r"\b(?:" + _PRODUCT_NAMES + "|" + _PRODUCT_WORDS + r")\b", sentence)
                and _MASSIVE_TRANSFUSION.search(sentence) is None
                and not (_RED_CELL_HISTORY.search(sentence) or _RED_CELL_PLAN.search(sentence)
                         or _CONDITIONAL.search(sentence) or _NOT_THE_RESIDENTS_ORDER.search(sentence)
                         or re.match(r"(?:samu|ems|prehospital\w*|en\s+ruta|ambulancia|traslado)\b", sentence))):
            actions.append(_clarification("Write each blood product with its own number of units."))
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
        # A repeat instruction after its order (DF-16b): the order runs now, and
        # the repeat -- interval, count and condition -- is kept as a plan.
        repeated = _repeat_split(sentence)
        if repeated is not None:
            head, clause = repeated
            # "Salbutamol 5 mg nbz, si persiste el broncoespasmo, repetir cada 20
            # minutos": the condition written between the order and its repeat
            # is the repeat's. Left with the order, the order became conditional
            # and the first dose was never given (DF-22, C01/C03).
            between = re.search(r",\s*((?:if|si|unless|salvo\s+que|en\s+caso\s+de)\b[^,]*)$", head)
            if between and _orders_now(head[:between.start()]):
                clause = between[1].strip() + ", " + clause
                head = head[:between.start()].strip(" ,")
            standalone = not head or not _orders_now(head)
            if standalone:
                # "Si persiste el broncoespasmo, repetir salbutamol en 20
                # minutos": what comes first is the repeat's own condition.
                clause = sentence
            # An order of its own written after the repeat is not part of it.
            segments = re.split(r",\s*(?:(?:y|e|and|then|luego)\s+)?", clause)
            own = next((i for i, segment in enumerate(segments) if _REPEAT_START.search(segment)), 0)
            for index in range(own + 1, len(segments)):
                if _orders_now(segments[index]):
                    queue.insert(0, ", ".join(segments[index:]))
                    clause = ", ".join(segments[:index])
                    break
            structure = repeat_structure(clause)
            # Alone, a repeat is a plan only when it is scheduled or conditional,
            # or follows an order in this entry. Otherwise it is given again now.
            if structure and (not standalone or last_order or set(structure) - {"after_min"}):
                if standalone:
                    keep(clause, "repeat", of=last_order, **structure)
                    continue
                trailing_advice.append((clause, "repeat", {"of": _repeat_target(head, clause), **structure}))
                sentence = head
        conditional = _CONDITIONAL.search(sentence)
        # A "when" inside what the resident saw is no condition: "Mareada cuando la PA baja a
        # 80/50, SF 500 ml ev" and "Presyncope when BP drops below 90 on standing, epinephrine
        # 0.5 mg IM now" lost their order without a word (post hoc, adversarial review of cycle
        # 8). The sentence reads on as it did before the cycle, and a condition after it counts.
        while conditional and _describes_what_was_seen(sentence, conditional):
            conditional = _CONDITIONAL.search(sentence, conditional.end())
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
                trailing_advice.append(re.sub(r"^(?:,\s*|(?:y|e|and)\s+)", "", sentence[advice.start():]))
                # The conjunction that introduced the advice goes with it.
                sentence = re.sub(r"(?:,\s*)?\b(?:and|y|then|luego)\s*$", "",
                                  sentence[:advice.start()].strip(" ,")).strip(" ,")
                if not sentence:
                    continue
            elif boundary:
                keep(sentence[conditional.start():], "conditional")
                sentence = sentence[:boundary.start()].strip(" ,")
                if not sentence:
                    continue
            else:
                # "A y B si C": the condition belongs to B. "Le doy colacion oral y
                # la doy de alta si la tolera" kept the snack back with the
                # discharge (2026-09-25). A head that is itself an order runs; the
                # rest is the plan.
                split = None
                contingency_split = False
                # "Then" parts them too: "NS 500 mL bolus now then repeat when SBP < 90" gives the
                # bolus now (post hoc, adversarial review of cycle 8).
                for match in re.finditer(r",\s*|\s+(?:y|e|and|then|luego)\s+", sentence[:conditional.start()]):
                    split = match
                if split and not sentence[split.end():conditional.start()].strip():
                    # "Start oxygen NC 3 L/min, if saturation falls": nothing stands
                    # between the comma and the condition, so it qualifies the order.
                    # Unless the condition is followed by an order of its own:
                    # "atropina 1 mg ev, si no responde, marcapaso" gives the atropine
                    # now and keeps the pacing as the plan. Read as one conditional,
                    # the first-line drug was never given (DF-22, C01, 2026-09-28).
                    contingency = _CONTINGENCY.match(sentence[conditional.start():])
                    head = sentence[:split.start()].strip(" ,")
                    # A head the reader cannot execute but that is written as an
                    # order ("transfundir 2 U de GR O negativo, si sigue
                    # hipotenso, ...") is read on its own: held and asked about,
                    # not folded into the plan where it vanished.
                    # A condition that runs on into its own order without a comma is one too:
                    # "Salbutamol 5 mg NBZ ahora, cuando la sat baje de 92% repetir" gave nothing
                    # now (post hoc, adversarial review of cycle 8).
                    then = contingency["then"] if contingency else _order_inside(sentence[conditional.end():])
                    # Only up to the next condition: each "si no, X" read the
                    # whole rest of the sentence again, twice, and the time
                    # doubled with every one (adversarial review of cycle 6).
                    following = _CONDITIONAL.search(then, 1)
                    if following:
                        then = then[:following.start()]
                    # Without the comma only the resident's own order parts from its plan: "En el SAMU le
                    # dieron atropina 0,5 mg ev, si no respondía iban a iniciar dopamina" is an account.
                    if not ((contingency and (_orders_now(head) or _an_instruction(head))
                             or (then and not contingency and _orders_now(head)))
                            and _an_instruction(then)):
                        split = None
                    else:
                        contingency_split = True
                head = (re.sub(r"\s+(?:y|e|and)$", "", sentence[:split.start()].strip(" ,"))
                        if split else "")
                # A head is an order whether or not it opens with a verb: chart
                # shorthand ("SF 500 ml ev y noradrenalina si persiste
                # hipotensa") ran nothing, the whole sentence became a plan
                # (DF-16b, 2026-09-28).
                if head and (_orders_now(head) or (contingency_split and _an_instruction(head))):
                    keep(sentence[split.end():].strip(" ,"), "conditional")
                    sentence = head
                else:
                    # A conditional order is a plan and is kept as one, whatever
                    # form the order takes: "lo doy de alta si tolera la via oral"
                    # and "si baja la PA, SF 500 ml ev" vanished without a word
                    # (2026-09-25).
                    bare = _CONDITION_CLAUSE.sub(" ", sentence).strip(" ,:")
                    if not bare:
                        # A condition written without a comma runs on into its order: "when hgb
                        # drops below 7 transfuse 1 unit PRBC", "whenever she gets drowsy or pCO2
                        # >45 -> call ICU". The order is where an order verb, or a discharge said
                        # as a clearance, starts; the whole was lost without a word (post hoc,
                        # blind set of cycle 8).
                        clause = sentence[conditional.end():]
                        bare = next((clause[start.end():] for start in re.finditer(r"(?:^|\s|->|→|=>)\s*(?=[a-z])", clause)
                                     if _COMMAND.match(clause[start.end():]) or _OK_DISCHARGE_TAIL.match(clause[start.end():])),
                                    "")
                    # Advice to the patient in a sentence of its own is advice, as it is after
                    # the discharge in the same sentence: "Lo doy de alta. Regresar si tiene
                    # fiebre." lost the advice without a word (cycle 8).
                    if _RETURN_ADVICE.match(sentence):
                        keep(sentence, "advice")
                        continue
                    # What the condition leads to needs only to be an instruction, not an order
                    # the reader can run: "Once MAP is above 65: stop the bolus and run NS at
                    # 100 mL/h", "if bleeding continues, place a second one proximal to the
                    # first", "Si persiste hipotensa, agregar vancomicina 25 mg/kg ev" and
                    # "once his fingerstick glucose drops below 70, push 50 mL of D50 IV" were
                    # lost without a word (TD-29 and TD-30, found comparing with the V2 reader,
                    # cycle 8). An instruction is an order verb, a verb with a medicine or a
                    # quantity, or a substance with the quantity given. Someone else's account
                    # is not one, and "if" after "check", "decidir" or "preguntar" is
                    # "whether". It applies only where the condition governs the whole
                    # sentence: it opens it, or nothing parts it from the order ("platelets if
                    # count < 50"). In "PA 76/46, sangrado arterial - pasar 2 UGR ahora, O neg
                    # si no hay tipificada" it qualifies one clause, and a plan of the whole
                    # would misname the order before it, which is not read.
                    before = sentence[:conditional.start()].strip(" ,")
                    whole = not before or not (re.search(r"[,;:]|\s+(?:y|e|and|then|luego)\s+", before)
                                               or re.search(r"[,;:]", sentence[conditional.start():]))
                    instruction = whole and bool(bare and bare != sentence and (_COMMAND.match(bare) or _OK_DISCHARGE_TAIL.match(bare) or (
                        _INSTRUCTION_START.match(bare) and (_names_a_drug(bare) or _QUANTITY.search(bare))) or (
                        _ADMINISTERED_QUANTITY.search(bare) and _names_a_substance(bare)) or (
                        # "Platelets if count < 50", "plaquetas si recuento < 50" (TD-32, cycle 8).
                        # "Plts if < 50k", "plaq 1 U c/10 kg si recuento < 50 mil" (post hoc,
                        # blind set of cycle 8).
                        re.fullmatch(r"(?:(?:\d+|one|two|una|dos)\s+(?:u|units?|unidades?|pools?|bolsas?)\s+(?:de\s+|of\s+)?)?"
                                     r"(?:" + _PRODUCT_NAMES + r"|" + _PRODUCT_WORDS + r"|plts?|plaq|" + _RED_CELL_WORDS + r")"
                                     r"(?:\s+(?:\d+\s*(?:u|units?|unidades?|pools?|bolsas?)|now|ahora|c/\s*\d+\s*kg|"
                                     r"(?:por|per)\s+(?:cada\s+)?\d+\s*kg|\d+\s*ml/kg))*", bare)))
                        and not _NOT_THE_RESIDENTS_ORDER.search(bare)
                        and not _WHETHER.search(sentence[:conditional.start()]))
                    # Tranexamic acid is read only where it opens its clause
                    # (C08), so a plan such as "if it keeps oozing, run the
                    # second gram of TXA over 8 hours" was no longer kept; it is
                    # kept as before (comparison with cycle 5, 2026-09-28).
                    if _TXA_WORD.search(bare) or _COMMAND.search(re.sub(r"^.*?[, :]", "", sentence)) or re.search(
                            r"\b(?:give|dar|doy|administrar|administro|start|iniciar|inicio|order|solicitar|"
                            r"solicito|pido|reassess|reevaluar|reevaluo|alta|hospitalizar|hospitalizo|"
                            r"ingresar|ingreso|trasladar|traslado|admit|discharge|transfer)\b", sentence) or (
                            bare and bare != sentence and _orders_now(bare)) or instruction:
                        keep(sentence, "conditional")
                    continue
        # Safety-netting written without "if" lists what should bring the patient
        # back: "return precautions for fever, vomiting or uncontrolled pain".
        # Split at its commas, only "fever" stayed with the advice and the rest
        # was read as nothing, where "regresar si tiene fiebre, vomitos o dolor
        # incontrolable" was kept whole (EN/ES measurement, 2026-09-27).
        listed = _LISTED_ADVICE.search(sentence)
        if listed:
            trailing_advice.append(sentence[listed.start():].strip(" ,"))
            sentence = re.sub(r"(?:,\s*)?\b(?:and|y|e|then|luego)\s*$", "",
                              sentence[:listed.start()].strip(" ,")).strip(" ,")
            if not sentence:
                continue
        inherited = None
        negated = False
        # Do not split the clinical device name "bag and mask", nor the blood
        # bank's two-word requests: "grupo" alone is not a study (2026-09-24).
        sentence = re.sub(r"\bbag and mask\b", "bag-mask", sentence)
        sentence = re.sub(r"\bhigh and tight\b", "high_and_tight", sentence)
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
        discharged = False
        # A discharge home in this sentence: the medicines listed after it with a regimen for
        # home are its prescriptions (post hoc, blind set of cycle 8).
        home_discharge = False
        # Each item of this sentence and what it produced, for a route written
        # once after a list of doses (_share_trailing_route).
        members = []
        # The blood product this sentence just recorded, which a count written
        # after it completes.
        kept_blood = None
        opened = len(actions)
        # The prehospital team's account, once a clause of this sentence gave
        # one (_PREHOSPITAL_ACCOUNT), and where the last item ended. A label
        # naming the ambulance is one from the start: "En ruta: 1 U GR O negativo
        # y TXA 1 g", "Prehospital: tourniquet, 1 unit whole blood" (adversarial
        # review of cycle 7).
        account = bool(re.match(r"(?:samu|ems|prehospital\w*|pre-?hospital\w*|en\s+ruta|en\s+route|ambulancia|"
                                r"ambulance|paramedic\w*|paramedico\w*)\s*:", sentence))
        told = None
        cursor = 0
        # "Once blood arrives, 2 units O-neg", "en cuanto llegue, 2 U GR": the
        # red cells after such a clause wait for it, and are asked about.
        waiting = False
        for piece in grouped:
            if told is not None and told[0] and not any(
                    action.get("type") not in {"clarification", "reassessment"} for action in actions[told[1]:]):
                account = True
            told = (bool(piece) and bool(_PREHOSPITAL_ACCOUNT.match(piece.strip()))
                    and bool(_TOLD_IN_THE_PAST.search(piece)), len(actions))
            found = sentence.find(piece, cursor) if piece else -1
            joined_by_and = found >= 0 and bool(re.fullmatch(r"[\s,]*(?:and|y|e)\s*", sentence[cursor:found]))
            if found >= 0:
                cursor = found + len(piece)
            # A bullet before an order is no part of it: "ortostatismo+ - iniciar 3
            # UGR ahora" (post hoc, blind set of cycle 7).
            piece = re.sub(r"^[\-–—•]+\s*", "", piece)
            members.append([piece, []])
            if not piece:
                continue
            dash = re.search(r"\s[-–—]\s+", piece)
            if dash and not _COMMAND.match(piece) and _COMMAND.match(piece[dash.end():]):
                heard = parse_family_actions(piece[:dash.start()])
                if not heard["actions"] and not heard["future_details"]:
                    # "Shock - transfundir 4 GR stat": what leads the dash is the
                    # reason, and the order after it is read (post hoc, blind set).
                    piece = members[-1][0] = piece[dash.end():]
            if re.match(r"(?:when|once|cuando|en\s+cuanto|as\s+soon\s+as|apenas|una\s+vez\s+que|after|despues\s+de|"
                        r"tras)\b", piece.strip()):
                waiting = True
            if _WEIGHT_STATEMENT.match(piece):
                # "pesa 62 kg" is what the resident knows about the patient, and
                # weight_based_doses reads it; it is not an order.
                continue
            finding = _STATUS_FINDING.match(piece)
            if finding and not _COMMAND.match(piece):
                # "HR 132 - give 2 units PRBC now", "FC 128: pasar 2 U de GR": the
                # finding leads an order of its own, and the whole clause was taken
                # for the finding, so the order was lost without a word beside
                # another one (A–J of cycle 7, independent set). What follows the
                # finding is read when it opens with an order verb; "satura 86%
                # con la naricera" is still the finding alone.
                led = re.sub(r"^[\s%\-–—:;>]+", "", piece[finding.end():])
                if led and _COMMAND.match(led):
                    piece = members[-1][0] = led
                else:
                    # A finding lends no verb and takes none (C09).
                    inherited = None
                    continue
            if _ED_OBSERVATION.search(piece) and not _ELSEWHERE.search(piece):
                # Observation in the emergency department is a destination with a
                # duration. Ordering it is not completing it (decision 4).
                hours = _OBSERVATION_HOURS.search(piece)
                actions.append({"type": "disposition", "destination": "ED observation",
                                "duration_h": float(hours.group(1).replace(",", ".")) if hours else None})
                if _MONITOR_WORDS.search(piece):
                    actions.append({"type": "monitoring"})
                discharged = True
                inherited = None
                continue
            if discharged and _DISCHARGE_ADVICE.match(piece):
                keep(piece.strip(), "advice")
                inherited = None
                continue
            # What is given before the patient leaves is no prescription: "Alta a domicilio, salbutamol
            # 4 puff ahora antes de irse", "tonight ceftriaxone 1 g IV q24h" (post hoc, adversarial
            # review of cycle 8).
            if home_discharge and _HOME_REGIMEN.search(piece) and (_names_a_drug(piece) or _UNMODELED_ORDER.search(piece)) \
                    and not re.search(r"\b(?:now|ahora|ya|stat|tonight|esta\s+noche|here|aqui|antes\s+de\s+(?:irse|salir|"
                                      r"que\s+se\s+vaya)|before\s+(?:he|she|they)?\s*(?:leaves?|goes|going|discharge)|"
                                      r"iv|ev|im|io|intravenous\w*|endovenos\w*|intramuscular\w*)\b", piece):
                # "Ok para alta, control en APS en 48 h, prednisona 40 mg x 5 días, salbutamol 2
                # puff c/6 h": what goes home with the patient is a prescription, recorded and
                # never given here. The steroid was asked its route, and the question held the
                # discharge (post hoc, blind set of cycle 8; "alta con..." was read so since
                # cycle 6, KD-06).
                keep(re.sub(r"^(?:then|luego|despues|and|y)\s+", "", piece.strip()), "not_modelled")
                details[-1].update({"kind": "prescription", "prescription": True})
                members[-1][1] = []
                inherited = None
                continue
            if _NEGATED_FINDING.match(piece):
                # A finding, not a negation: what follows it is read ("sin acceso
                # venoso: EZ-IO tibial"), and it negates nothing after it.
                parts = re.split(r"\s*(?::|\s[-–—]\s|->)\s*", piece, maxsplit=1)
                if len(parts) == 2 and parts[1].strip():
                    piece = members[-1][0] = parts[1].strip()
                else:
                    inherited = None
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
            # The massive transfusion protocol and the blood products the engine
            # does not run: recorded as ordered, with their effect not modelled,
            # and the other orders run (TD-26, 2026-09-28). The red cells written
            # with them are still an order of their own; nothing becomes red
            # cells, and no unit or ratio is invented.
            own = _COMMAND.match(piece.strip())
            here = own["verb"] if own else inherited
            anothers = account or bool(_NOT_THE_RESIDENTS_ORDER.search(piece))
            item = re.sub(r"^(?:then|luego|despues|and|y)\s+", "", piece.strip())
            if (not anothers and len(members) > 1 and re.fullmatch(
                    r"(?:activate(?:\s+it)?|activar(?:lo)?|activalo|activenlo|activemos(?:lo)?|lo\s+activ(?:o|amos))"
                    r"(?:\s+(?:now|ya|ahora))?\s*[.!]?", item)
                    and _MASSIVE_TRANSFUSION.search(members[-2][0])
                    and not re.search(r"\b(?:no|not|sin|without|never|nunca|ya|already|activad[oa]|activated)\b|n't\b",
                                      members[-2][0])):
                # "Meets MTP criteria, activate": the protocol just named is the one
                # activated. Its activation was lost without a word (post hoc, cycle 7).
                piece = members[-1][0] = item = "activate mtp"
                own, here = _COMMAND.match(piece), "activate"
            # What completes the order just written: the count of the product
            # ("pasar crioprecipitado ahora, unas 10 unidades del pool"), the
            # protocol's cooler ("activate the MTP, get the cooler up here"), where
            # the measure goes ("tourniquet on that leg, right above the wound").
            # Each was quoted back as an order of its own and held the rest (A–J of
            # cycle 7, independent set).
            if not anothers and kept_blood is not None and kept_blood == len(details) - 1 and \
                    _A_COUNT_ALONE.fullmatch(item):
                details[kept_blood]["text"] = future[kept_blood] = future[kept_blood] + ", " + item
                continue
            if not anothers and _BLOOD_COOLER.search(item) and not (
                    red_cells_named(item) or unmodelled_blood_product(item, here)
                    or massive_transfusion_activation(item) is not None):
                if protocol_kept is not None:
                    details[protocol_kept]["text"] = future[protocol_kept] = future[protocol_kept] + ", " + item
                    members[-1][1] = []
                else:
                    ran = [_clarification("Specify which blood product to give and how many units.")]
                    actions.extend(ran)
                    members[-1][1] = ran
                inherited = None
                continue
            timing = _BLOOD_TIMING.fullmatch(item)
            previous_blood = next((action for action in (members[-2][1] if len(members) > 1 else [])
                                   if action.get("type") == "blood" and action.get("units")), None)
            if timing and previous_blood is not None:
                # "Transfundir 2 U GR, pasar en 2 hrs c/u": the time the units run in, written
                # as a clause of its own, was quoted back and held the transfusion (post hoc,
                # blind set of cycle 8). Each unit's time adds up when it is per unit.
                minutes = float(timing["value"].replace(",", ".")) * (
                    60 if timing["unit"].startswith(("h", "hora", "hour")) else 1)
                if timing["each"]:
                    minutes *= previous_blood["units"]
                previous_blood["administration_duration_min"] = minutes
                members[-1][1] = members[-2][1]
                continue
            if len(members) > 1 and any(action.get("type") == "epinephrine_im" or str(action.get("route") or "").upper()
                                        in {"IM", "SC"} for action in members[-2][1]) \
                    and _INJECTION_SITE.fullmatch(item):
                # "Give IM epi, anterolateral thigh": where the injection goes, quoted back as an
                # order of its own that held the rest (TD-31, cycle 8).
                members[-1][1] = members[-2][1]
                continue
            if len(members) > 1 and any(action.get("type") == "hemorrhage_control" for action in members[-2][1]) \
                    and _WHERE_THE_MEASURE_GOES.fullmatch(item):
                # It stays with the measure, and so does the next one: "deep and tight".
                members[-1][1] = members[-2][1]
                continue
            if not anothers and _MTP_STOP.search(item) and not _MTP_STOP_NOT_NOW.search(sentence):
                # "Deactivate MTP", "stand down the MTP", "suspender PTM": recorded as the
                # protocol stood down, never as an activation or nothing at all (TD-32, cycle 8).
                keep(item, "not_modelled")
                members[-1][1] = []
                inherited = None
                continue
            activation = None if anothers else massive_transfusion_activation(piece)
            product = None if anothers else unmodelled_blood_product(piece, here, own=bool(own))
            if activation is not None or product:
                written = re.sub(r"^(?:then|luego|despues|and|y)\s+", "", piece.strip())
                if activation is not None:
                    # The activation as written, then what it was written with.
                    cut = written.rfind(activation) if activation else -1
                    keep(written[:cut].strip(" ,:") if cut > 0 else written, "not_modelled")
                    protocol_kept = len(details) - 1
                    rest = re.sub(r"^(?:(?:activad[oa]|activated|activation|now|ahora|ya|stat|immediately|"
                                  r"inmediatamente|with|con|and|y|plus|mas|\+)\b[\s:,]*|[:,]\s*)+", "",
                                  activation.strip())
                    segments = [part for part in re.split(r"\s*(?:,|\+|\band\b|\by\b|\bwith\b|\bcon\b|\bplus\b|"
                                                          r"\bmas\b)\s*", rest) if part.strip()] if rest else []
                    lent = "transfuse"
                else:
                    segments = [part for part in re.split(
                        r"\s+(?:con|with|mas|plus|junto\s+con|along\s+with)\s+", written) if part.strip()]
                    lent = here
                ran = []
                for segment in segments:
                    # Each product keeps what it is: plasma recorded, red cells run
                    # in the units written, anything else read as the order it is.
                    # "Transfuse 2 units FFP with TXA 1 g IV" and "Activate MTP with
                    # TXA 1 g IV" recorded the tranexamic acid as a medicine not
                    # modelled, and it was never given (adversarial review of cycle 7).
                    other = unmodelled_blood_product(segment, lent, own=activation is None and bool(own)) \
                        or (re.search(r"\b(?:" + _PRODUCT_NAMES + "|" + _PRODUCT_WORDS + r")\b", segment)
                            and activation is not None)
                    red = red_cells_named(segment, lent) or (activation is not None
                                                             and bool(_RED_CELL_QUALIFIER.search(segment)))
                    if red and other:
                        # "GR/PFC 2 U c/u": which product the count belongs to is
                        # the resident's to say (TD-26, D).
                        ran = [_clarification("Write each blood product with its own number of units.")]
                        break
                    if other:
                        keep(segment if len(segments) > 1 or activation is not None else written, "not_modelled")
                    elif red:
                        ran.append({"type": "blood", "units": blood_units(segment)})
                    else:
                        read, _ = _parse_piece(segment, None)
                        ran.extend(read)
                actions.extend(ran)
                members[-1][1] = ran
                last_order = sentence
                # What follows an activation is read on its own: "Activate MTP, 4
                # units O-neg" asked which specialist to call (adversarial review).
                inherited = None if activation is not None else here
                kept_blood = len(details) - 1 if details and not ran else None
                continue
            attached = None if anothers else _ATTACHED_PLAN.search(piece)
            # "Alta con adrenalina autoinyectable" is the autoinjector the patient goes home with (post
            # hoc, adversarial review of cycle 8); given now, "autoinyectable" is read as before.
            if (attached and (_UNMODELED_ORDER.search(piece[attached.end():])
                              or re.search(r"\bauto-?(?:inyect|inject)able\b", piece[attached.end():]))
                    and not _UNMODELED_ORDER.search(piece[:attached.start()])):
                head_actions, _ = _parse_piece(piece[:attached.start()], here)
                if any(action.get("type") == "disposition" and action.get("destination") == "home"
                       for action in head_actions):
                    # "Discharge home with an EpiPen prescription": the discharge runs, and
                    # what the patient goes home with is its prescription. The prescription
                    # took the whole clause and the discharge was lost without a word (found
                    # with KD-05, cycle 8).
                    keep(piece[attached.end():].strip(" ,"), "not_modelled")
                    details[-1].update({"kind": "prescription", "prescription": True})
                    members[-1][1] = head_actions
                    actions.extend(head_actions)
                    discharged = True
                    last_order = sentence
                    inherited = None
                    continue
            if _UNMODELED_ORDER.search(piece) or _unmodelled_dextrose(piece):
                # Recognised and not something this version executes: recorded as
                # the resident's indication, with its administration and effect
                # not modelled, and the other orders run (2026-09-24; faculty
                # decision 3, 2026-09-25). A prescription for home is a
                # prescription, never a dose given here. The word that joined it
                # to the list is not part of it ("y después ondansetrón…").
                keep(re.sub(r"^(?:then|luego|despues|and|y)\s+", "", piece.strip()), "not_modelled")
                # Still a dose in the list: a route written after it is shared.
                members[-1][1] = [{"agent": "not_modelled", "route": _route(piece), "listed_only": True}]
                last_order = sentence
                inherited = None
                continue
            if inherited in _STOP_VERBS and (
                    (_QUANTITY.search(piece) and not _DETERMINER_START.match(piece.strip()))
                    or _PATIENT_STATEMENT.match(piece.strip())):
                inherited = None
            # A bleeding measure or an intraosseous line written with what is given
            # beside it: "Tourniquet with TXA 1 g IV", "Humeral IO with 2 units
            # O-neg". One was read and the other lost without a word (adversarial
            # review of cycle 7). "Pack the wound with hemostatic gauze" is one measure.
            joined = [part for part in re.split(r"\s+(?:with|plus|mas|junto\s+con|along\s+with|con)\s+", item)
                      if part.strip()]
            if len(joined) > 1 and not anothers and (_haemorrhage_measures(joined[0]) or _IO_ACCESS.search(joined[0])) \
                    and any(_TXA_WORD.search(part) or _names_a_drug(part) or red_cells_named(part)
                            or re.search(r"\b(?:saline|ns|sf|ringer|lr|crystalloid|cristaloides?|suero|fluids?)\b", part)
                            for part in joined[1:]):
                parsed = []
                for number, part in enumerate(joined):
                    parsed.extend(_parse_piece(part, inherited if number == 0 else None)[0])
                inherited = None
            else:
                parsed, inherited = _parse_piece(piece, inherited)
            if waiting and any(action.get("type") == "blood" for action in parsed):
                # "Once blood arrives, 2 units O-neg", "After the CT, transfuse 2
                # units PRBC": red cells that wait for something are asked about,
                # never run now (adversarial review of cycle 7).
                parsed = [_clarification("Specify whether to transfuse these units now, with the number "
                                         "of units, or to request a crossmatch to have them reserved.")]
            item = re.sub(r"^(?:then|luego|despues|and|y)\s+", "", piece.strip())
            if not parsed and len(grouped) == 1 and _BARE_IO.fullmatch(item):
                # "Vía intraósea" written as the whole order is the line; after a
                # dose ("ceftriaxona 2 g, IO") it is that dose's route (C7-06).
                parsed = [{"type": "vascular_access", "operation": "start", "access": "intraosseous"}]
            if (re.match(r"(?:i|we)\s+(?!will\b|want\s+to\b|am\s+going\b)", item) and parsed
                    and all(action.get("type") == "clarification" and action.get("unrecognized_text")
                            for action in parsed)
                    and not (_names_a_drug(item) or _QUANTITY.search(item))):
                # The first person opens an order only when it names one (C07).
                # "We give it 5 minutes", "we continue to observe the MAP" are
                # prose, read as before: quoted back as unrecognized orders, they
                # held the epinephrine written before them (adversarial review of
                # cycle 6).
                parsed, inherited = [], None
            if (account and (joined_by_and or not _COMMAND.match(item)) and not _RESIDENT_AS_SUBJECT.match(item)
                    and any(action.get("type") not in {"clarification", "reassessment"} for action in parsed)):
                parsed, inherited = [_part_of_an_account(item)], None
            elif any(action.get("type") not in {"clarification", "reassessment"} for action in parsed):
                account = False
            # Nothing read, or only a question the verb of an item before it
            # raised ("monitor + IV"): a listed set-up item is still its own order.
            lent_verb_only = (len(parsed) == 1 and parsed[0].get("type") == "clarification"
                              and not _COMMAND.match(item))
            if (not parsed or lent_verb_only) and (len(grouped) > 1 or several_sentences):
                support = _verbless_support(item)
                if support is not None:
                    parsed, inherited = [support], None
            previous = members[-2][1] if len(members) > 1 else None
            if (previous and len(previous) == 1 and previous[0].get("type") == "blood"
                    and previous[0].get("units") is None):
                # "Go to blood, 2 units of O-neg", "pasa a GR O Rh negativo, 2
                # unidades": one transfusion and its count, never two orders --
                # the count answered later would have given the units twice (TD-26).
                count = re.fullmatch(r"(?:(\d+)|(una|un|uno|one|dos|two|tres|three|cuatro|four))\s*"
                                     r"(?:u|units?|unidad(?:es)?|bolsas?|bags?)\.?", item)
                if len(parsed) == 1 and parsed[0].get("type") == "blood" and parsed[0].get("units") is not None:
                    previous[0]["units"], parsed = parsed[0]["units"], []
                elif count and all(action.get("type") == "clarification" for action in parsed):
                    previous[0]["units"] = float(count[1]) if count[1] else float(_UNIT_WORDS[count[2]])
                    parsed = []
            members[-1][1] = parsed
            if any(action.get("type") not in {"clarification", "reassessment"} for action in parsed):
                last_order = sentence
            discharged = discharged or any(action.get("type") == "disposition" for action in parsed)
            if any(action.get("type") == "disposition" and action.get("destination") == "home"
                   for action in parsed):
                home_discharge = True
                # The plan written into the discharge order itself is the same
                # advice as the plan listed after it: "discharge him with
                # orthopedic follow-up" and "lo doy de alta con control en
                # policlinico" executed the discharge and lost the follow-up,
                # in both languages, where ", control urologico" was kept
                # (DF-10, 2026-09-27). Anything else it is written with ("with
                # his wife", "con paracetamol") is left as it was.
                for attached in _ATTACHED_PLAN.finditer(piece):
                    plan = piece[attached.end():].strip(" ,")
                    if _DISCHARGE_ADVICE.match(plan):
                        keep(plan, "advice")
                        break
                    if _names_a_drug(plan):
                        # "Alta con paracetamol 1 g c/8 h": what the patient goes
                        # home with is a prescription, recorded and never given
                        # here. It was lost with no word (KD-06; DF-22, C05).
                        keep(plan, "prescription")
                        break
            if (reasoning_head and len(parsed) == 1 and parsed[0].get("type") == "clarification"
                    and str(parsed[0].get("message", "")).startswith("The requested study")):
                # The rest of a stated priority is not a request for a study.
                inherited = None
                continue
            actions.extend(parsed)
        # Two red-cell orders in one sentence are one order whose count is asked:
        # "2 U GR ahora y 2 U GR en 1 hora" and "Transfuse PRBC 2 units, O-neg 2
        # units" ran four units at once (adversarial review of cycle 7).
        bloods = [index for index in range(opened, len(actions)) if actions[index].get("type") == "blood"]
        if len(bloods) > 1:
            actions[bloods[0]] = {"type": "blood", "units": None}
            for index in reversed(bloods[1:]):
                del actions[index]
        _share_trailing_route(members, sentence)
    flush_trailing_advice()
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
        details.extend(deferred.get("future_details", []))
    return {"raw_text": raw, "actions": _quoted_as_written(actions, raw), "recognized_future_actions": future,
            "future_details": details}


def _quoted_as_written(actions, raw):
    """An unreadable order is quoted as the resident wrote it, not as the reader normalised it.

    "Pasó tranexámico" was quoted back as "administrar tranexamico" (TD-28, cycle 8). The
    words the reader kept are found again in what was written: each matches its written word
    once accents and case are set aside, or is the infinitive the reader read an imperative
    as. Where no written span matches well enough, the quote stays as it was.
    """
    written = [(match, _normalize(match.group(0)).strip(".,;:!?()\"'¿¡")) for match in re.finditer(r"\S+", raw)]
    for action in actions:
        fragment = action.get("unrecognized_text") if isinstance(action, dict) else None
        if not fragment:
            continue
        # The reader's own joined tokens ("type_and_screen", "grupo_y_pruebas") are words the
        # resident wrote apart; unsplit, a question quoted the token (post hoc, adversarial review of
        # cycle 8).
        words = [word.strip(".,;:!?()\"'") for word in fragment.replace("_", " ").split()]
        best = None
        for start in range(0, len(written) - len(words) + 1):
            window = written[start:start + len(words)]
            same = [word == key or _ES_IMPERATIVE_FORMS.get(key) == word for word, (_, key) in zip(words, window)]
            if same[0] and same[-1] and sum(same) >= max(1, round(0.6 * len(words))) and (
                    best is None or sum(same) > best[0]):
                best = (sum(same), window[0][0].start(), window[-1][0].end())
        if best is None:
            continue
        quoted = " ".join(raw[best[1]:best[2]].split()).rstrip(".,;:")[:80]
        if quoted and quoted != fragment:
            action["message"] = action["message"].replace(f'"{fragment}"', f'"{quoted}"', 1)
            action["unrecognized_text"] = quoted
    return actions


# A route written once after a list of doses belongs to every dose of the list:
# "salbutamol 5 mg + ipratropio 0.5 mg nbz", "morphine 4 mg and ondansetron 4 mg
# IV". Only the last dose kept it, and the order was held asking for a route the
# resident had written (DF-16a, 2026-09-28). The route goes back over the doses
# written just before it without one of their own; a dose with its own route,
# an item that is not a dose, or a sequence ("then", "luego") ends the list.
_SEQUENCE_WORDS = re.compile(r"\b(?:then|luego|despues|after\s+that|afterwards|posteriormente)\b")


def _takes_the_route(item):
    piece, parsed = item
    return (len(parsed) == 1 and bool(parsed[0].get("agent")) and "route" in parsed[0]
            and parsed[0].get("route") is None and _route(piece) is None
            and (parsed[0].get("listed_only") or any(key.startswith("dose") for key in parsed[0])))


def _share_trailing_route(members, sentence):
    if _SEQUENCE_WORDS.search(sentence):
        return
    for end in range(len(members) - 1, 0, -1):
        piece, parsed = members[end]
        if len(parsed) != 1 or not parsed[0].get("agent") or not parsed[0].get("route") \
                or _route(piece) != parsed[0]["route"]:
            continue
        # A route written before its drug is that drug's own ("aspirin 300 mg, IV
        # morphine 4 mg"): it was not written after the list, and the dose before
        # it keeps what its own words say (KD-01, 2026-09-28).
        if re.match(r"(?:(?:and|y|e|plus|mas|\+)\s+)?" + ROUTE_BEFORE_THE_DRUG + r"\s+", piece.strip()):
            continue
        index = end - 1
        while index >= 0 and _takes_the_route(members[index]):
            if not members[index][1][0].get("listed_only"):
                members[index][1][0]["route"] = parsed[0]["route"]
            index -= 1


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
