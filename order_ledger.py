"""Every order the resident writes ends with one recorded fate (Phase 0, workstream 0A).

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit found orders that
disappeared without the resident being told: an insulin written beside the dextrose it
was given with, a transfusion typed in the answer to a held order, an antibiotic the
legacy path did not know. The patient then evolved as if the order had never been
written, and the record could be read as an omission the resident did not commit.

This module does not read orders: the reader does (``family_parser``, frozen since V3,
and the legacy reader for PS001). It checks what the reader returned against what the
resident wrote, and gives every order one fate:

* ``EXECUTED`` -- the engine carried it out;
* ``HELD_CLARIFICATION`` / ``HELD_REASONING`` -- waiting on an answer or on the reasoning
  the gate asks for; nothing ran;
* ``RECORDED_NOT_MODELLED`` -- recognised and recorded as the resident's decision; this
  simulator does not model its administration or effect (or its future timing);
* ``UNRECOGNIZED`` -- the reader did not understand it; nothing ran;
* ``SCHEDULED`` -- waiting for a result the resident said to wait for;
* ``CANCELLED`` -- cancelled by the resident, or discarded when a new order replaced it;
* ``DUPLICATE_IGNORED`` / ``DUPLICATE_CONFIRMED`` -- a repeated submission or service call;
* ``TERMINAL_NOT_EXECUTABLE`` -- written after an arrest this pilot does not manage.

The detector of actionable text is deliberately broader than the reader's lexicon: it
knows drugs, procedures and studies the reader does not, and a dose written beside an
unknown word. What it flags and the reader produced nothing for becomes an
``UNRECOGNIZED`` order, so nothing the resident wrote can vanish between the text and the
engine. It never executes anything and never makes the reader read more.
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from copy import deepcopy

LEDGER_SCHEMA = "order_ledger_v1"

FATES = ("EXECUTED", "HELD_CLARIFICATION", "HELD_REASONING", "RECORDED_NOT_MODELLED", "UNRECOGNIZED",
         "SCHEDULED", "CANCELLED", "DUPLICATE_IGNORED", "DUPLICATE_CONFIRMED", "TERMINAL_NOT_EXECUTABLE")
HELD = frozenset({"HELD_CLARIFICATION", "HELD_REASONING"})
#: Fates after which nothing more will happen to the order in this encounter.
FINAL = frozenset(FATES) - HELD - {"SCHEDULED"}
#: Fates under which the order did not act on the patient, for a reason that is not the
#: resident's choice: an omission can never be read from them.
NOT_ACTED = frozenset(FATES) - {"EXECUTED", "DUPLICATE_CONFIRMED", "CANCELLED", "DUPLICATE_IGNORED"}

SPAN_CLASSES = ("clinical_order", "reassessment_wait", "reasoning", "commentary", "non_actionable",
                "actionable_unrecognized")


def fold(text):
    """Lower case without accents, so one pattern serves both languages."""
    return _fold_map(text)[0]


def _fold_map(text):
    """The folded text and, for each folded character, its index in the original."""
    raw = str(text or "")
    folded, index = [], []
    for position, char in enumerate(raw):
        plain = unicodedata.normalize("NFKD", char).encode("ascii", "ignore").decode("ascii").lower()
        if not plain and not char.isspace() and not unicodedata.combining(char):
            plain = " "  # a symbol with no ASCII form still separates words
        for piece in plain:
            folded.append(piece)
            index.append(position)
    return "".join(folded), index


def new_id():
    return uuid.uuid4().hex[:12]


# --------------------------------------------------------------------------------------
# The detector's vocabulary. Each entry: what it names, how it is written, what kind of
# thing it is, and which reader actions count as having understood it. An entry with no
# action types is something no engine here executes: it is accounted for only when the
# reader itself quoted it as unrecognised or recorded it as a plan or a decision.
# --------------------------------------------------------------------------------------
def _entry(key, pattern, kind, types=(), agent=None, cls=None):
    return {"key": key, "pattern": re.compile(r"(?<![a-z0-9])(?:" + pattern + r")(?![a-z0-9])"),
            "kind": kind, "types": frozenset(types), "agent": agent, "cls": cls or kind}


def _reader_agents():
    """The reader's own medicines, read from its table (never changed here)."""
    try:
        from family_parser import _AGENTS
    except Exception:  # pragma: no cover - the reader is part of the repository
        return []
    related = {
        "dextrose": ("dextrose", "dextrose_infusion"),
        "naloxone": ("naloxone", "naloxone_infusion"),
        "bronchodilator": ("bronchodilator", "continuous_bronchodilator"),
        "procedural_sedation": ("procedural_sedation", "sedation_infusion"),
        "anticoagulation": ("anticoagulation", "infusion_adjustment"),
    }
    out = []
    for cls, agents in _AGENTS.items():
        for name, pattern in agents.items():
            out.append(_entry(name, pattern, "drug", related.get(cls, (cls,)),
                              agent=name if len(agents) > 1 else None, cls=cls))
    return out


def _reader_studies():
    try:
        from family_parser import _DIAGNOSTICS
    except Exception:  # pragma: no cover
        return []
    return [_entry(key, pattern, "study", ("diagnostic",), agent=key, cls="study")
            for key, pattern in _DIAGNOSTICS.items()]


_INFUSION = ("infusion_adjustment",)
_EXTRA = [
    # Vasoactive drugs, haemostatics and glucose the reader runs under their own action type.
    _entry("norepinephrine", r"norepinephrine|norepinefrina|noradrenalin[ae]|norepi|levophed", "drug",
           ("norepinephrine",) + _INFUSION, cls="vasopressor"),
    _entry("epinephrine", r"(?<!nor)epinephrine|(?<!nor)epinefrina|(?<!nor)adrenalin[ae]|epi(?![- ]?pen)", "drug",
           ("epinephrine_im", "epinephrine_bolus", "epinephrine", "epinephrine_infusion") + _INFUSION,
           cls="vasopressor"),
    _entry("dobutamine", r"dobutamin[ae]", "drug", ("dobutamine",) + _INFUSION, cls="inotrope"),
    _entry("nitroglycerin", r"nitroglycerin\w*|nitroglicerina|ntg|trinitrina|nitro", "drug",
           ("nitroglycerin", "nitroglycerin_bolus") + _INFUSION, cls="vasodilator"),
    _entry("tranexamic acid", r"tranexamic\w*|tranexamico|txa", "drug", ("tranexamic_acid",), cls="haemostatic"),
    _entry("oral carbohydrate", r"oral\s+glucose|glucosa\s+oral|jugo|juice|azucar\s+oral", "drug",
           ("oral_carbohydrate",), cls="glucose"),
    # Medicines no engine here executes. The reader records some as unmodelled decisions
    # (diphenhydramine, famotidine, ondansetron); others it quotes, and one written beside
    # another order it may not mention at all (insulin "with dextrose", 2026-10-06).
    _entry("vasopressin", r"vasopres+in\w*|vasopresina|pitressin", "drug", cls="vasopressor"),
    _entry("phenylephrine", r"phenylephrine|fenilefrina", "drug", cls="vasopressor"),
    _entry("dopamine", r"dopamin[ae]", "drug", cls="vasopressor"),
    _entry("insulin", r"insulin[ae]?", "drug", cls="insulin"),
    _entry("sodium bicarbonate", r"bicarbonat\w*|bicarb|nahco3", "drug", cls="electrolyte"),
    _entry("potassium chloride", r"potassium\s+chloride|cloruro\s+de\s+potasio|kcl", "drug", cls="electrolyte"),
    _entry("cefepime", r"cefepim\w*", "drug", cls="antibiotics"),
    _entry("meropenem", r"meropenem\w*", "drug", cls="antibiotics"),
    _entry("imipenem", r"imipenem\w*", "drug", cls="antibiotics"),
    _entry("ertapenem", r"ertapenem\w*", "drug", cls="antibiotics"),
    _entry("cefazolin", r"cefazolin\w*", "drug", cls="antibiotics"),
    _entry("cefotaxime", r"cefotaxim\w*", "drug", cls="antibiotics"),
    _entry("ceftazidime", r"ceftazidim\w*", "drug", cls="antibiotics"),
    _entry("ampicillin", r"ampicil+in\w*|ampicilina", "drug", cls="antibiotics"),
    _entry("amoxicillin", r"amoxicil+in\w*|amoxicilina", "drug", cls="antibiotics"),
    _entry("clindamycin", r"clindamycin|clindamicina", "drug", cls="antibiotics"),
    _entry("metronidazole", r"metronidazol\w*", "drug", cls="antibiotics"),
    _entry("gentamicin", r"gentamicin\w*|gentamicina", "drug", cls="antibiotics"),
    _entry("amikacin", r"amikacin\w*|amikacina", "drug", cls="antibiotics"),
    _entry("levofloxacin", r"levofloxacin\w*|levofloxacino", "drug", cls="antibiotics"),
    _entry("ciprofloxacin", r"ciprofloxacin\w*|ciprofloxacino", "drug", cls="antibiotics"),
    _entry("linezolid", r"linezolid\w*", "drug", cls="antibiotics"),
    _entry("doxycycline", r"doxycyclin\w*|doxiciclina", "drug", cls="antibiotics"),
    _entry("acyclovir", r"acyclovir|aciclovir", "drug", cls="antiviral"),
    _entry("labetalol", r"labetalol", "drug", cls="antihypertensive"),
    _entry("nicardipine", r"nicardipin[ae]", "drug", cls="antihypertensive"),
    _entry("hydralazine", r"hydralazin[ae]|hidralazina", "drug", cls="antihypertensive"),
    _entry("esmolol", r"esmolol", "drug", cls="beta_blocker"),
    _entry("adenosine", r"adenosin[ae]|adenosina", "drug", cls="antiarrhythmic"),
    _entry("digoxin", r"digoxin[ae]?|digoxina", "drug", cls="antiarrhythmic"),
    _entry("lidocaine", r"lidocain[ae]|lidocaina", "drug", cls="antiarrhythmic"),
    _entry("levetiracetam", r"levetiracetam|keppra", "drug", cls="anticonvulsant"),
    _entry("phenytoin", r"(?:fos)?phenytoin|(?:fos)?fenitoina", "drug", cls="anticonvulsant"),
    _entry("haloperidol", r"haloperidol", "drug", cls="antipsychotic"),
    _entry("hydromorphone", r"hydromorphone|hidromorfona", "drug", cls="opioid_analgesia"),
    _entry("vitamin K", r"vitamin[ae]?\s+k|phytonadione|fitomenadiona", "drug", cls="reversal"),
    _entry("prothrombin complex", r"pcc|prothrombin\s+complex|complejo\s+protrombinico|octaplex|kcentra", "drug",
           cls="reversal"),
    _entry("protamine", r"protamin[ae]|protamina", "drug", cls="reversal"),
    _entry("idarucizumab", r"idarucizumab|praxbind", "drug", cls="reversal"),
    _entry("flumazenil", r"flumazenil", "drug", cls="reversal"),
    _entry("activated charcoal", r"activated\s+charcoal|carbon\s+activado", "drug", cls="decontamination"),
    _entry("acetylcysteine", r"acetylcysteine|acetilcisteina|n-acetylcysteine", "drug", cls="antidote"),
    _entry("mannitol", r"mannitol|manitol", "drug", cls="osmotic"),
    _entry("hypertonic saline", r"hypertonic\s+saline|suero\s+hipertonico|solucion\s+hipertonica", "drug",
           cls="osmotic"),
    _entry("terbutaline", r"terbutalin[ae]|terbutalina", "drug", cls="bronchodilator"),
    _entry("antihistamine", r"diphenhydramine|difenhidramina|clorfenamina|chlorphenamine|antihistamin\w*", "drug",
           cls="antihistamine"),
    _entry("H2 blocker", r"famotidin[ae]|ranitidin[ae]", "drug", cls="h2_blocker"),
    _entry("antiemetic", r"ondansetron|metoclopramid[ae]", "drug", cls="antiemetic"),
    _entry("benzodiazepine", r"lorazepam|diazepam|clonazepam|alprazolam", "drug", cls="benzodiazepine"),
    _entry("blood product", r"ffp|fresh\s+frozen\s+plasma|plasma\s+fresco|pfc|platelets?|plaquetas|cryo\w*|crio\w*",
           "drug", cls="blood_product"),
    # Fluids, blood and oxygen as the reader runs them.
    _entry("crystalloid", r"ringer'?s?\s+lactat\w*|ringer\s+lactato|lactato\s+de\s+ringer|lactated\s+ringer'?s?|"
                          r"ringer\w*|hartmann|normal\s+saline|saline|plasma-?lyte|"
                          r"suero\s+fisiologico|solucion\s+fisiologica|cristaloides?|crystalloids?|ns|lr|sf|rl",
           "fluid", ("fluid",), cls="fluid"),
    _entry("red cells", r"prbcs?|packed\s+(?:red\s+)?(?:blood\s+)?cells|red\s+(?:blood\s+)?cells|globulos\s+rojos|"
                        r"hematies|transfus\w*|transfund\w*|o-?neg\w*|o\s+negativ\w*|uncross\w*|"
                        r"unidades?\s+de\s+sangre|units?\s+of\s+blood", "blood", ("blood",), cls="blood"),
    _entry("oxygen", r"oxygen|oxigeno|o2|non-?rebreather|nrb|nasal\s+cannula|canula\s+nasal|naricera|venturi|"
                     r"high[- ]flow|alto\s+flujo|hfnc", "support", ("oxygen", "niv"), cls="oxygen"),
    _entry("non-invasive ventilation", r"bipap|cpap|niv|non-?invasive\s+ventilation|"
                                       r"ventilacion\s+(?:mecanica\s+)?no\s+invasiva|vmni",
           "support", ("niv",), cls="ventilation"),
    _entry("bag-mask ventilation", r"bag[- ]?(?:valve[- ])?mask|bvm|ambu|bolsa[- ]mascarilla", "support",
           ("bag_mask",), cls="ventilation"),
    _entry("intubation", r"intubat\w*|intubar\w*|intubacion|rsi|secuencia\s+rapida|endotracheal|"
                         r"tubo\s+endotraqueal", "procedure",
           ("intubation", "airway_preparation", "invasive_ventilation", "respiratory_adjustment"), cls="airway"),
    # Procedures.
    _entry("transcutaneous pacing", r"pacing|marcapas\w*|pacer|transcutaneous", "procedure",
           ("transcutaneous_pacing",), cls="rhythm"),
    _entry("cardioversion", r"cardiover\w*|synchroni[sz]ed\s+shock|choque\s+sincronizado", "procedure",
           ("cardioversion",), cls="rhythm"),
    _entry("CPR / defibrillation", r"cpr|rcp|chest\s+compressions?|compresiones(?:\s+toracicas)?|"
                                   r"cardiopulmonary\s+resuscitation|reanimacion\s+cardiopulmonar|acls|"
                                   r"defibrillat\w*|desfibril\w*", "procedure", cls="resuscitation"),
    _entry("chest decompression", r"needle\s+decompression|thoracostomy|chest\s+tube|tubo\s+pleural|pleurostomia|"
                                  r"toracostomia|descompresion", "procedure", ("chest_decompression",),
           cls="thoracic"),
    _entry("haemorrhage control", r"tourniquets?|torniquetes?|direct\s+pressure|presion\s+directa|packing|"
                                  r"empaquet\w*|hemostatic\w*", "procedure", ("hemorrhage_control",),
           cls="haemorrhage"),
    _entry("pelvic binder", r"pelvic\s+binder|binder\s+pelvico|faja\s+pelvica|cinturon\s+pelvico", "procedure",
           ("pelvic_binder",), cls="haemorrhage"),
    _entry("vascular access", r"iv\s+access|iv\s+line|peripheral\s+(?:iv|line)|vascular\s+access|acceso\s+venoso|"
                              r"via\s+venosa|vvp|large[- ]bore|intraosseous|intraose\w*|(?:humeral|tibial|sternal)\s+io|"
                              r"io\s+(?:access|line|needle|cannula)", "procedure",
           ("vascular_access",), cls="access"),
    _entry("central or arterial line", r"central\s+(?:venous\s+)?line|cvc|cateter\s+venoso\s+central|"
                                       r"arterial\s+line|linea\s+arterial|art\s+line", "procedure", cls="access"),
    _entry("urinary catheter", r"foley|urinary\s+catheter|sonda\s+(?:vesical|foley|urinaria)|cateter\s+urinario",
           "procedure", ("urinary_catheter",), cls="support"),
    _entry("gastric tube", r"ng\s+tube|nasogastric|sonda\s+nasogastrica|sng|orogastric", "procedure",
           ("gastric_tube",), cls="support"),
    _entry("lumbar puncture", r"lumbar\s+puncture|puncion\s+lumbar", "procedure", cls="procedure"),
    _entry("pericardiocentesis", r"pericardiocentesis", "procedure", cls="procedure"),
    # Studies the reader does not know (its own come from its table).
    _entry("echocardiogram", r"echocardiogra\w*|ecocardiogra\w*|echo", "study", cls="imaging"),
    _entry("MRI", r"mri|resonancia(?:\s+magnetica)?", "study", cls="imaging"),
]

# Services, as they are named after "call", "consult", "page", "llamar a".
_SERVICES = {
    "cardiology": ("cardio", "cardiologia", "cardiologist", "cardiologo"),
    "cath lab": ("cath", "hemodinamia", "catheterization", "cateterismo"),
    "gastroenterology": ("gastro", "gi", "gastroenterologist", "gastroenterologo", "endoscopy", "endoscopia"),
    "surgery": ("surgery", "surgeon", "cirugia", "cirujano", "general surgery", "trauma surgery"),
    "urology": ("urology", "urologia", "urologist", "urologo"),
    "icu": ("icu", "uci", "uti", "upc", "intensive care", "cuidados intensivos", "intensivist", "intensivista"),
    "neurology": ("neuro", "neurology", "neurologia", "neurologist"),
    "nephrology": ("nephro", "nephrology", "nefrologia", "dialysis", "dialisis"),
    "pulmonology": ("pulmonology", "neumologia", "respiratory therapy"),
    "anaesthesia": ("anesthesia", "anaesthesia", "anestesia", "anestesiologia", "anesthesiologist"),
    "orthopaedics": ("ortho", "orthopedics", "orthopaedics", "traumatologia", "traumatologo"),
    "interventional radiology": ("interventional radiology", "ir", "radiologia intervencional"),
    "toxicology": ("toxicology", "poison control", "cituc", "toxicologia"),
    "obstetrics": ("obstetrics", "obgyn", "ob/gyn", "ginecologia", "obstetricia"),
    "operating room": ("operating room", "or", "pabellon", "quirofano", "theatre"),
}
_CONSULT = re.compile(r"(?<![a-z])(?:call|consult|consultar|page|contact|notify|ask|interconsult\w*|"
                      r"llam\w*(?:\s+a)?|avis\w*(?:\s+a)?|activ\w*|solicit\w*\s+(?:evaluacion|interconsulta)"
                      r"(?:\s+(?:de|por|a))?)\s+(?:the\s+|a\s+|al\s+|a\s+la\s+|la\s+|el\s+|on-?call\s+)?"
                      r"([a-z/\-]+(?:\s+[a-z]+)?)")


def lexicon():
    global _LEXICON
    if _LEXICON is None:
        # The reader's own words first: a mention it reads is matched against its own actions.
        _LEXICON = _reader_agents() + _reader_studies() + _EXTRA
    return _LEXICON


_LEXICON = None

# Order cues. An imperative or infinitive at the head of a clause, a dose, or a route.
_FILLERS = re.compile(r"^(?:\s|please|now|then|also|and|so|ok|okay|stat|immediately|next|first|"
                      r"let'?s|lets|we\s+will|we'?ll|i\s+will|i'?ll|i\s+would\s+like\s+to|i\s+want\s+to|"
                      r"we\s+need\s+to|need\s+to|plan\s+to|going\s+to|gonna|"
                      r"por\s+favor|favor|ahora|luego|despues|tambien|ademas|primero|y|e|entonces|"
                      r"vamos\s+a|voy\s+a|hay\s+que|quiero|necesito|vamos|indico|indicar|se\s+indica)+")
_ORDER_VERB = re.compile(
    r"(?:give|start|begin|initiate|commence|administer|push|infuse|transfuse|bolus|run|hang|load|"
    r"call|consult|page|contact|request|order|obtain|get|draw|send|check|recheck|repeat|perform|do|"
    r"intubate|insert|place|apply|put|activate|admit|transfer|discharge|stop|hold|increase|decrease|"
    r"titrate|wean|switch|change|add|prepare|set|use|continue|resume|book|arrange|"
    r"dar|dale|denle|darle|doy|damos|administr\w*|inici\w*|comenz\w*|comienz\w*|pon\w*|pas\w*|coloc\w*|instal\w*|"
    r"llam\w*|avis\w*|solicit\w*|ped\w*|pid\w*|tom\w*|hac\w*|realiz\w*|intub\w*|insert\w*|"
    r"activ\w*|hospitaliz\w*|ingres(?:ar|e|en|a|amos|o)|traslad\w*|suspend\w*|deten\w*|aument\w*|disminu\w*|baj\w*|"
    r"sub\w*|titul\w*|cambi\w*|agreg\w*|prepar\w*|usar|continu\w*|mant\w*|repet\w*|"
    r"transfund\w*|cargar|carg\w*|infund\w*|dej\w*)(?![a-z])")
_DOSE = re.compile(
    r"(?<![a-z0-9.,])\d+(?:[.,]\d+)?\s*(?:mcg/kg/min|mcg/kg/h|mcg/min|mg/kg/h|mg/kg|mcg/kg|ml/kg|ml/h|"
    r"units?/kg/h|units?/kg|units?/h|u/kg|mcg|ug|mg|gr|grams?|gramos?|g|units?|unidades?|ui|iu|u|"
    r"meq|mmol|ml|cc|litros?|liters?|litres?|l|joules?|j)(?![a-z/])(?!\s*/\s*(?:dl|l)(?![a-z]))")
_ROUTE = re.compile(r"(?<![a-z])(?:iv(?!\s+(?:access|line|lines|fluids?|catheter|cannula|site|pole|bag))|ev|im|io|sc|po|sl|neb\w*|intraven\w*|intramuscul\w*|subcut\w*|"
                    r"sublingual|endoven\w*|nebuli[sz]\w*)(?![a-z])")
_REASONING = re.compile(
    r"(?<![a-z])(?:i\s+think|i\s+believe|i\s+suspect|i\s+expect|i\s+am\s+worried|i'?m\s+worried|"
    r"i\s+am\s+concerned|i'?m\s+concerned|concern(?:ed)?\s+(?:for|about)|probably|likely|consistent\s+with|"
    r"because|due\s+to|since|given\s+that|the\s+priority|my\s+priority|working\s+(?:model|diagnosis)|"
    r"differential|expect|expected|should\s+(?:improve|rise|fall|increase|decrease|help|respond)|"
    r"responded|response|improved|worsened|after\s+(?:the|his|her)|creo|pienso|sospecho|espero|porque|"
    r"debido\s+a|ya\s+que|dado\s+que|me\s+preocupa|probablemente|la\s+prioridad|mi\s+prioridad|"
    r"diagnostico|deberia\s+(?:mejorar|subir|bajar|responder)|respondio|respuesta|mejoro|empeoro|"
    r"tras\s+(?:el|la|los|las))(?![a-z])")
_NEGATION = re.compile(r"(?<![a-z])(?:do\s+not|don'?t|no|not|avoid|without|hold\s+off|withhold|never|"
                       r"sin|evitar|evito|nunca|tampoco)(?![a-z])")
_HISTORY = re.compile(r"(?<![a-z])(?:received|already\s+(?:got|had|received|given)|took|takes|taking|was\s+given|"
                      r"were\s+given|prehospital|pre-?hospital|ems\s+gave|home\s+medications?|"
                      r"recibio|ya\s+recibio|toma|tomaba|usa|usaba|le\s+dieron|le\s+pusieron|in\s+place|in\s+situ|"
                      r"already\s+in|already\s+on|ya\s+tiene|ya\s+esta\s+con|instalad[oa]s?)(?![a-z])")
_STATUS_AFTER = re.compile(r"(?<![a-z])(?:given|administered|started|done|completed|activated|not\s+given|"
                           r"registrad[oa]|administrad[oa]|iniciad[oa]|puest[oa]|pending|pendiente|deferred|"
                           r"declined|appreciated|diferid[oa]|rechazad[oa])(?![a-z])")
_INTERROGATIVE = re.compile(r"^\s*(?:do|does|did|are|is|have|has|any|what|when|how|which|why|tiene|tuvo|hay|"
                            r"que|cuando|como|cual|donde)(?![a-z])")
_WAIT_WORDS = re.compile(r"(?<![a-z])(?:reassess\w*|re-?evaluat\w*|reevalu\w*|wait\w*|esper\w*|observ\w*|"
                         r"vital\s+signs?|signos\s+vitales|vitals)(?![a-z])")
# "Espero que suba la presión" is an expectation; "esperar 20 minutos" is a wait.
_EXPECTATION = re.compile(r"(?<![a-z])(?:espero|esperamos|esperaria|se\s+espera|i\s+hope|hopefully)\s+(?:que|that|the|it|he|she)?"
                          r"(?![a-z])")
_SENTENCE = re.compile(r"(?:(?<!\d)[.](?!\d)|[;\n!?])+")
_CLAUSE = re.compile(r",|(?<![a-z])(?:and|y|e|plus|mas|then|luego|despues|also|tambien|ademas|as\s+well\s+as)"
                     r"(?![a-z])|\+")


def _clauses(text):
    """(sentence, terminator, clause, start) for each clause, with offsets in the folded text."""
    folded, _ = _fold_map(text)
    out = []
    start = 0
    for match in list(_SENTENCE.finditer(folded)) + [None]:
        end = match.start() if match else len(folded)
        sentence = folded[start:end]
        terminator = match.group(0) if match else ""
        piece_start = 0
        for clause_match in list(_CLAUSE.finditer(sentence)) + [None]:
            piece_end = clause_match.start() if clause_match else len(sentence)
            clause = sentence[piece_start:piece_end]
            if clause.strip():
                out.append((sentence, terminator, clause, start + piece_start))
            piece_start = clause_match.end() if clause_match else len(sentence)
        start = match.end() if match else len(folded)
    return folded, out


def _head(clause):
    """The clause without its leading fillers ("please", "let's", "vamos a")."""
    return _FILLERS.sub("", clause).lstrip(" :-")


def _signature(action):
    keys = ("type", "agent", "agent_name", "diagnostic", "requested_diagnostic", "service", "destination",
            "device", "fluid_type", "support_type", "region", "measure", "target")
    return " ".join(fold(action.get(key)) for key in keys if action.get(key))


_INFUSABLE = frozenset({"norepinephrine", "epinephrine", "dobutamine", "nitroglycerin", "dextrose", "naloxone",
                        "heparin", "propofol", "midazolam", "dexmedetomidine", "ketamine", "insulin",
                        "vasopressin", "phenylephrine", "dopamine", "magnesium sulfate"})


def _covers(entry, action):
    pending = action.get("pending_action") if isinstance(action.get("pending_action"), dict) else None
    if pending and _covers(entry, pending):
        return True
    kind = action.get("type")
    if kind == "repeat_order" and entry["kind"] in ("drug", "fluid", "blood"):
        # A repeat names the drug it repeats, or the kind of order it repeats.
        named = fold(action.get("agent") or "")
        target = str(action.get("target") or "")
        if named:
            return fold(entry["agent"] or entry["key"]) in named or named in fold(entry["key"])
        if target:
            return target in entry["types"] or (target == "fluid" and entry["kind"] == "fluid")
        return True
    if kind == "infusion_adjustment" and entry["kind"] == "drug":
        named = fold(action.get("agent") or "")
        return (fold(entry["agent"] or entry["key"]) in named) if named else entry["key"] in _INFUSABLE
    if not entry["types"] or kind not in entry["types"]:
        return False
    if entry["kind"] == "study":
        return entry["agent"] in (action.get("diagnostic"), action.get("requested_diagnostic"))
    if entry["agent"]:
        return fold(entry["agent"]) in _signature(action)
    return True


def _quoted(parsed):
    """Everything the reader itself said about the text: quotes, plans, unmodelled decisions."""
    out = []
    for action in parsed.get("actions") or []:
        if isinstance(action, dict) and action.get("type") == "clarification":
            out.append(fold(action.get("unrecognized_text") or ""))
            out.append(fold(action.get("message") or ""))
    out.extend(fold(text) for text in parsed.get("recognized_future_actions") or [])
    out.extend(fold(detail.get("text")) for detail in parsed.get("future_details") or [] if isinstance(detail, dict))
    out.extend(fold(detail.get("text")) for detail in parsed.get("ledger_plans") or [] if isinstance(detail, dict))
    return [" ".join(text.split()) for text in out if text.strip()]


def _generic_questions(parsed):
    """The reader's questions that name no item: they hold whatever they are about."""
    return [action for action in parsed.get("actions") or []
            if isinstance(action, dict) and action.get("type") == "clarification"
            and not action.get("unrecognized_text") and not action.get("pending_action")]


_CONDITION_HEAD = re.compile(r"^(?:once|when|whenever|if|unless|until|after|before|as\s+soon\s+as|cuando|si|"
                             r"una\s+vez(?:\s+que)?|hasta\s+que|tras|despues\s+de|antes\s+de|apenas|al\s+llegar)"
                             r"(?![a-z])")
_HISTORY_HEAD = re.compile(r"^(?:so\s+far|balance|ingresos|egresos|total|in\s+total|after|s/p|status\s+post|"
                           r"post|hasta\s+ahora|tras|despues\s+de|on\s+arrival|al\s+ingreso)(?![a-z])")
_BEFORE_MENTION = re.compile(r"(?<![a-z])(?:because|since|as\s+(?:he|she|it|the|his|her|bp|they)|when|whenever|if|"
                             r"for|to\s+(?:treat|rule\s+out|exclude|cover|prevent|reverse)|in\s+case|"
                             r"porque|ya\s+que|dado\s+que|cuando|si|por\s+si|para|en\s+caso|after|despues\s+de|tras)(?![a-z])")
_TRAILING_NEGATION = re.compile(r"(?<![a-z])(?:but\s+not|not\s+now|not\s+yet|pero\s+no|ahora\s+no|todavia\s+no|"
                                r"aun\s+no|for\s+now\s+no|still\s+not)(?![a-z])")
_ROUTE_CONTEXT = re.compile(r"(?<![a-z])(?:por|por\s+la|por\s+el|via|through|through\s+the|in\s+the|en\s+la|"
                            r"en\s+el|by|with)\s*$")
_PARAMETER_WORDS = frozenset({"tidal", "volume", "volumen", "corriente", "peep", "fio2", "frequency", "frecuencia",
                              "rate", "flow", "flujo", "pressure", "presion", "ipap", "epap", "mode", "modo",
                              "ventilator", "ventilador", "settings", "plateau", "meseta", "inspiratory",
                              "inspiratorio", "support", "soporte", "real", "peso", "weight", "ideal", "predicted",
                              "kg", "gauge", "calibre", "bore"})
_GAUGE = re.compile(r"(?<![a-z0-9])\d+\s*g(?:auge)?\s*(?=(?:iv|ivs|angio\w*|cath\w*|cannula\w*|line|access|bore|"
                    r"venflon|branula|bajo)(?![a-z]))")


def _service_of(word):
    """The service a call names ("cardiología" → cardiology), or None."""
    word = fold(word).strip()
    first = word.split(" ")[0] if word else ""
    for service, names in _SERVICES.items():
        for name in names:
            if word == name or word.startswith(name + " ") or first == name or \
                    (len(name) >= 5 and first[:5] == name[:5]):
                return service
    return None


def _clause_class(sentence, terminator, clause):
    head = _head(clause)
    if not head.strip(" ,"):
        return "non_actionable"
    verb = _ORDER_VERB.match(head)
    if "?" in terminator or (_INTERROGATIVE.match(head) and not verb):
        return "commentary"
    if _NEGATION.match(head):
        return "commentary"
    if _EXPECTATION.search(clause) and not verb:
        return "reasoning"
    if _WAIT_WORDS.search(clause) and not (verb and _DOSE.search(clause)):
        return "reassessment_wait"
    if _REASONING.search(clause) and not verb:
        return "reasoning"
    if (_HISTORY.search(clause) or _HISTORY_HEAD.match(head)) and not verb:
        return "commentary"
    if verb or _DOSE.search(clause) or _ROUTE.search(clause):
        return "clinical_order"
    return "commentary"


def _raw(text, index, begin, end):
    """The resident's own words for a folded span (accents and case kept)."""
    raw = str(text or "")
    if not index:
        return ""
    begin = min(max(begin, 0), len(index) - 1)
    end = min(max(end, begin + 1), len(index))
    piece = raw[index[begin]:index[end - 1] + 1]
    return " ".join(piece.split()).strip(" ,;:.")


def _clause_of(pieces, at):
    for piece in pieces:
        sentence, terminator, clause, start = piece
        if start <= at < start + len(clause):
            return piece
    return None


def coverage(text, parsed):
    """Map the text into clauses and find what the reader produced nothing for.

    Returns ``{"spans": [...], "unaccounted": [...], "held": [...]}``. A mention is
    actionable when its clause is an order (an imperative at its head, a dose, a route, or
    a list carried by an order verb at the head of the sentence) and it is not negated,
    not a question, not a condition, not reasoning or purpose ("because", "for"), and not
    the history of what the patient received before. An actionable mention is accounted
    for when the reader returned an action that names it, quoted it, or recorded it as a
    plan or an unmodelled decision. One the reader did not account for is ``held`` when
    the reader asked a question that names no item (the question holds the order it is
    about), and ``unaccounted`` otherwise.
    """
    parsed = parsed or {}
    actions = [a for a in parsed.get("actions") or [] if isinstance(a, dict)]
    quoted = _quoted(parsed)
    folded, pieces = _clauses(text)
    index = _fold_map(text)[1]
    masked = _GAUGE.sub(lambda m: " " * len(m.group(0)), folded)
    led, reported, governed = {}, {}, {}
    for sentence, terminator, clause, start in pieces:
        if sentence not in led:
            first = _head(clause)
            led[sentence] = bool(_ORDER_VERB.match(first)) and not _REASONING.search(clause)
            # "Balance: 2 U GR, 2 L SF", "So far 2 units PRBC and 2 L crystalloid": a report of
            # what was given, in every clause of the sentence.
            reported[sentence] = (bool(_HISTORY_HEAD.match(first) or _HISTORY_HEAD.match(clause.strip()))
                                  and not _ORDER_VERB.match(first))
    previous = {}
    for sentence, terminator, clause, start in pieces:
        # What governs a clause: the nearest clause before it in the same sentence that had
        # a verb or was a reassessment or reasoning. "Reassess blood pressure and lactate in
        # 10 minutes": the lactate is part of the reassessment. "Espero que ... y suba la
        # glicemia": the expectation goes on, unless a dose makes the clause an order.
        own = _clause_class(sentence, terminator, clause)
        governed[start] = previous.get(sentence)
        if own in ("reassessment_wait", "reasoning") or _ORDER_VERB.match(_head(clause)):
            if not (previous.get(sentence) == "reasoning" and own == "clinical_order"
                    and not _DOSE.search(clause)):
                previous[sentence] = own
    # Mentions over the whole text, so a name written across a clause break ("type and
    # cross") is one mention; overlapping readings of the same words are one group.
    found = []
    for entry in lexicon():
        for match in entry["pattern"].finditer(masked):
            found.append((match.start(), match.end(), entry, match.group(0)))
    groups = []
    for begin, end, entry, word in sorted(found, key=lambda item: (item[0], -item[1])):
        if groups and begin < groups[-1]["end"]:
            groups[-1]["entries"].append(entry)
            if end > groups[-1]["end"]:
                groups[-1]["end"] = end
                groups[-1]["text"] = folded[groups[-1]["begin"]:end]
        else:
            groups.append({"begin": begin, "end": end, "entries": [entry], "text": word})
    consult_actions = [a for a in actions if a.get("type") in ("consult", "disposition", "reperfusion_referral")]
    consult_targets = [(m.start(), m.group(0), m.group(1)) for m in _CONSULT.finditer(folded)]
    spans_info = {}
    candidates = []
    for group in groups:
        piece = _clause_of(pieces, group["begin"])
        if piece is None:
            continue
        sentence, terminator, clause, start = piece
        relative = group["begin"] - start
        before = clause[:relative]
        head = _head(clause)
        span_class = _clause_class(sentence, terminator, clause)
        if governed.get(start) in ("reasoning", "reassessment_wait") and span_class in ("commentary",
                                                                                        "clinical_order") \
                and not _DOSE.search(clause) and not (span_class == "clinical_order" and governed.get(start) ==
                                                      "reassessment_wait" and _ORDER_VERB.match(head)):
            span_class = governed[start]
        listed = span_class == "commentary" and led.get(sentence)
        actionable = span_class == "clinical_order" or bool(listed)
        entries = group["entries"]
        covered = (any(_covers(entry, action) for entry in entries for action in actions)
                   or any(group["text"] in quote for quote in quoted))
        after = clause[relative + len(group["text"]):]
        skip = (not actionable or bool(_NEGATION.search(before)) or bool(_TRAILING_NEGATION.search(clause))
                or bool(_HISTORY.search(clause)) or bool(_HISTORY_HEAD.match(head))
                or bool(_CONDITION_HEAD.match(head)) or bool(_BEFORE_MENTION.search(before))
                or bool(_STATUS_AFTER.search(after)) or reported.get(sentence) or "?" in terminator)
        if all(e["kind"] == "study" for e in entries) and not _ORDER_VERB.match(head) and not listed:
            # A study named beside a number is a result ("Hb 7 g"), not a request.
            skip = True
        if any(e["key"] in ("vascular access", "central or arterial line") for e in entries) \
                and _ROUTE_CONTEXT.search(before):
            # "SF 500 mL por la VVP": the line the fluid runs through, not an order to place one.
            skip = True
        spans_info.setdefault(start, []).append({"key": entries[0]["key"], "kind": entries[0]["kind"],
                                                 "cls": entries[0]["cls"], "text": group["text"],
                                                 "covered": covered})
        if not skip and not covered:
            candidates.append((group, piece))
    # Consults: name matching where it works, and never fewer calls than were written.
    unmatched_actions = list(consult_actions)
    consult_flags = []
    for at, phrase, target in consult_targets:
        piece = _clause_of(pieces, at)
        if piece is None:
            continue
        sentence, terminator, clause, start = piece
        head = _head(clause)
        relative = at - start
        # Only a call written as an order: "Call surgery", "Llamar a cirugía", or a call in a
        # list an order verb opens. "Surgery consult deferred" is a note.
        ordered = bool(_ORDER_VERB.match(head)) and (relative <= len(clause) - len(clause.lstrip()) + 40)
        if not (ordered or led.get(sentence)) or "?" in terminator:
            continue
        if (bool(_NEGATION.search(clause[:relative])) or bool(_HISTORY.search(clause))
                or bool(_CONDITION_HEAD.match(head)) or bool(_STATUS_AFTER.search(clause[relative:]))
                or reported.get(sentence)):
            continue
        service = _service_of(target)
        stem = fold(target).split(" ")[0][:5]
        match = next((a for a in unmatched_actions
                      if service and (_service_of(a.get("service") or a.get("destination") or "") == service
                                      or service in _signature(a))), None)
        if match is None:
            match = next((a for a in unmatched_actions if stem and stem in _signature(a)), None)
        if match is None and service is None and not re.search(
                r"(?<![a-z])(?:call|consult|page|llam|avis|interconsult)", phrase):
            continue
        if match is None and unmatched_actions:
            # Never fewer calls recorded than were written; which name the reader gave a
            # call is the reader's reading, not a lost order.
            match = unmatched_actions[0]
        if match is None and any(fold(target) in quote for quote in quoted):
            continue
        if match is not None:
            unmatched_actions.remove(match)
        else:
            consult_flags.append((at, phrase, piece))
    held, unaccounted = [], []
    questions = _generic_questions(parsed)

    def add(item):
        (held if questions else unaccounted).append(item)

    # Adjacent mentions of one thing in one clause are one order ("oxygen via nasal cannula").
    merged = []
    for group, piece in candidates:
        if merged and merged[-1][1] == piece and merged[-1][0]["entries"][0]["cls"] == group["entries"][0]["cls"] \
                and not re.search(r"\d", folded[merged[-1][0]["end"]:group["begin"]]):
            merged[-1][0]["end"] = group["end"]
            continue
        merged.append(({**group, "entries": list(group["entries"])}, piece))
    for position, (group, piece) in enumerate(merged):
        sentence, terminator, clause, start = piece
        # Up to the next thing the clause names, read or not ("insulin 10 units IV" with
        # dextrose 25 g": the dextrose is not part of what was missed).
        later = [g["begin"] for g in groups if g["begin"] >= group["end"] and g["begin"] < start + len(clause)]
        end = min(later) if later else start + len(clause)
        span = folded[group["begin"]:end]
        span = re.sub(r"(?<![a-z])(?:with|con|and|y|plus|mas|then|luego|en|in|at|a|by|via|por)\s*$", "",
                      span.strip()).strip(" ,")
        entry = group["entries"][0]
        add({"text": _raw(text, index, group["begin"], group["begin"] + len(span)), "key": entry["key"],
             "cls": entry["cls"], "kind": entry["kind"], "at": group["begin"]})
    for at, phrase, piece in consult_flags:
        sentence, terminator, clause, start = piece
        add({"text": _raw(text, index, at, start + len(clause.rstrip())), "key": "consultation", "cls": "consult",
             "kind": "consult", "at": at})
    # A dose beside a word no vocabulary knows ("Give zyxin 2 g"): the reader must have
    # produced something for this clause, or it is unaccounted.
    for sentence, terminator, clause, start in pieces:
        if any(start <= g["begin"] < start + len(clause) for g in groups):
            continue
        head = _head(clause)
        listed = led.get(sentence) and not _ORDER_VERB.match(head)
        if not (_ORDER_VERB.match(head) or listed) or "?" in terminator:
            continue
        if _NEGATION.search(clause) or _HISTORY.search(clause) or _CONDITION_HEAD.match(head) \
                or _HISTORY_HEAD.match(head) or _TRAILING_NEGATION.search(clause):
            continue
        local = masked[start:start + len(clause)]
        dose = _DOSE.search(local)
        if not dose:
            continue
        words = re.findall(r"[a-z][a-z\-]{2,}", _head(local[:dose.start()]))
        unknown = [w for w in words if not _ORDER_VERB.fullmatch(w) and w not in _FILLER_WORDS
                   and w not in _PARAMETER_WORDS]
        if unknown and not _clause_is_covered(clause, actions, quoted):
            add({"text": _raw(text, index, start, start + len(clause.rstrip())), "key": unknown[-1],
                 "cls": "unknown", "kind": "unknown", "at": start})
    spans = []
    flagged = {item["at"] for item in held + unaccounted}
    for sentence, terminator, clause, start in pieces:
        span_class = _clause_class(sentence, terminator, clause)
        if any(start <= at < start + len(clause) for at in flagged):
            span_class = "actionable_unrecognized"
        spans.append({"text": _raw(text, index, start, start + len(clause.rstrip())), "class": span_class,
                      "mentions": spans_info.get(start, [])})
    return {"spans": spans, "unaccounted": _unique(unaccounted), "held": _unique(held)}


def _unique(items):
    seen, out = set(), []
    for item in items:
        marker = (item["text"].lower(), item["key"])
        if marker not in seen:
            seen.add(marker)
            out.append(item)
    return out


_FILLER_WORDS = frozenset({"the", "and", "with", "for", "now", "please", "then", "una", "uno", "las", "los", "del",
                           "por", "con", "para", "ahora", "luego", "dose", "dosis", "bolus", "bolo", "stat", "over",
                           "durante", "every", "cada", "minutes", "minutos", "hours", "horas", "min", "via",
                           "route", "slow", "lento", "push", "patient", "paciente", "him", "her", "another",
                           "more", "other", "otro", "otra", "mas", "additional", "second", "segundo", "repeat",
                           "fluid", "fluids", "liquido", "liquidos", "units", "unidades", "dosage", "single",
                           "unica", "total", "load", "loading", "carga", "infusion", "drip", "goteo", "velocidad",
                           "ampollas", "ampolla", "ampoules", "ampoule", "vial", "viales", "dosis", "una", "dos",
                           "tres", "one", "two", "three", "four", "cuatro", "half", "media", "medio"})


def _clause_is_covered(clause, actions, quoted):
    plain = " ".join(clause.split())
    words = {w for w in re.findall(r"[a-z0-9%]{2,}", plain) if w not in _FILLER_WORDS}
    for quote in quoted:
        if plain in quote or (quote and quote in plain):
            return True
        quote_words = set(re.findall(r"[a-z0-9%]{2,}", quote))
        if words and len(words & quote_words) >= max(2, round(0.6 * len(words))):
            return True
    return any(fold(action.get("agent") or action.get("type")).replace("_", " ") in plain for action in actions
               if action.get("type") not in {"clarification", "reassessment"})


# --------------------------------------------------------------------------------------
# Orders and their fates.
# --------------------------------------------------------------------------------------
def canonical(action):
    """A short, stable name for a reader action, for the record (not a clinical label)."""
    if not isinstance(action, dict):
        return ""
    parts = [str(action.get("type") or "")]
    for key in ("agent", "agent_name", "diagnostic", "service", "destination", "device", "fluid_type", "region",
                "measure", "operation"):
        if action.get(key) not in (None, "") and str(action.get(key)) not in parts:
            parts.append(str(action[key]))
    for key, unit in (("volume_ml", " mL"), ("dose_mg", " mg"), ("dose_g", " g"), ("dose", ""), ("rate", ""),
                      ("rate_mcg_min", " mcg/min"), ("flow_lpm", " L/min"), ("energy_j", " J"),
                      ("delay_min", " min")):
        value = action.get(key)
        if value not in (None, ""):
            parts.append(f"{value:g}{unit}" if isinstance(value, (int, float)) and not isinstance(value, bool)
                         else f"{value}{unit}")
    if action.get("type") == "blood" and action.get("units") is not None:
        parts.append(f"{action['units']:g} units" if isinstance(action["units"], (int, float)) else str(action["units"]))
    elif isinstance(action.get("units"), str):
        parts.append(action["units"])
    if action.get("route"):
        parts.append(str(action["route"]))
    return " ".join(part for part in parts if part)


def _mention_span(action, text):
    """Where in the resident's text an action came from, best effort (for the record)."""
    if action.get("type") == "clarification" and action.get("unrecognized_text"):
        return str(action["unrecognized_text"])
    folded, pieces = _clauses(text)
    index = _fold_map(text)[1]
    for sentence, terminator, clause, start in pieces:
        for entry in lexicon():
            if entry["pattern"].search(clause) and _covers(entry, action):
                return _raw(text, index, start, start + len(clause.rstrip()))
    if action.get("type") == "reassessment":
        for sentence, terminator, clause, start in pieces:
            if _WAIT_WORDS.search(clause):
                return _raw(text, index, start, start + len(clause.rstrip()))
    return ""


def order_from_action(action, *, submission_id, index, text, minute):
    action = action if isinstance(action, dict) else {}
    kind = action.get("type")
    return {
        "order_id": action.get("_order_id") or f"{submission_id}:{index}",
        "submission_id": action.get("_submission_id") or submission_id,
        "span": action.get("_span") or _mention_span(action, text),
        "canonical": canonical(action) if kind != "clarification" else "unrecognized",
        "class": ("reassessment" if kind == "reassessment" else
                  "unrecognized" if kind == "clarification" and action.get("unrecognized_text") else
                  "clarification" if kind == "clarification" else str(kind or "")),
        "dose": next((action.get(k) for k in ("dose_mg", "dose_g", "dose", "volume_ml", "energy_j")
                      if action.get(k) is not None), None),
        "route": action.get("route"),
        "rate": next((action.get(k) for k in ("rate", "rate_mcg_min", "flow_lpm") if action.get(k) is not None),
                     None),
        "timing": ({"delay_min": action.get("delay_min"), "wait": bool(action.get("wait"))}
                   if kind == "reassessment" else
                   {"after_result": action["after_result"]} if action.get("after_result") else None),
        "written_at_min": action.get("_written_at_min", minute),
        "fate": None,
        "reason": None,
        "executed_at_min": None,
        "receipt": None,
        "modelled_effect": None,
        "history": [],
    }


def tag(parsed, submission_id, text=None, minute=None):
    """Give each reader action a stable order id that travels with it through holds."""
    for index, action in enumerate(parsed.get("actions") or []):
        if isinstance(action, dict) and not action.get("_order_id"):
            action["_order_id"] = f"{submission_id}:{index}"
            action["_submission_id"] = submission_id
            if text is not None:
                action["_span"] = _mention_span(action, text)
            if minute is not None:
                action["_written_at_min"] = minute
    return parsed


def strip_tags(action):
    """An action as the engine receives it: the ledger's own keys removed."""
    if not isinstance(action, dict):
        return action
    return {key: value for key, value in action.items() if not str(key).startswith("_")}


def untagged(parsed):
    """A reader's result as the reader returned it: the ledger's keys removed (for the record)."""
    if not isinstance(parsed, dict):
        return parsed
    out = {key: deepcopy(value) for key, value in parsed.items() if not str(key).startswith("_")}
    out["actions"] = [strip_tags(deepcopy(a)) for a in parsed.get("actions") or []]
    return out


def set_fate(order, fate, reason=None, *, minute=None, receipt=None, modelled_effect=None):
    if fate not in FATES:
        raise ValueError(f"unknown fate {fate!r}")
    if order.get("fate") != fate or not order.get("history"):
        order.setdefault("history", []).append({"fate": fate, "minute": minute, "reason": reason})
    order["fate"] = fate
    order["reason"] = reason
    if receipt is not None:
        order["receipt"] = receipt
    if modelled_effect is not None:
        order["modelled_effect"] = modelled_effect
    if fate in ("EXECUTED", "DUPLICATE_CONFIRMED") and order.get("executed_at_min") is None:
        order["executed_at_min"] = minute
    return order


def unrecognized_receipt(span):
    return (f'Not understood: "{span}". Nothing was given or done for it. Write it again in other words '
            "if you still want it.")


def unaccounted_orders(cov, *, submission_id, minute, start=1000):
    """One UNRECOGNIZED order for each actionable text the reader produced nothing for."""
    out = []
    for offset, item in enumerate(cov.get("unaccounted") or []):
        order = {
            "order_id": f"{submission_id}:u{start + offset}",
            "submission_id": submission_id,
            "span": item["text"],
            "canonical": "unrecognized",
            "class": "unrecognized",
            "detected_as": item["cls"],
            "dose": None, "route": None, "rate": None, "timing": None,
            "written_at_min": minute, "fate": None, "reason": None, "executed_at_min": None,
            "receipt": None, "modelled_effect": False, "history": [],
        }
        set_fate(order, "UNRECOGNIZED", "not read by the simulator's reader; nothing was given", minute=minute,
                 receipt=unrecognized_receipt(item["text"]))
        out.append(order)
    return out


_PLAN_KINDS = {
    "not_modelled": ("RECORDED_NOT_MODELLED", "administration and effect not modelled in this simulator"),
    "prescription": ("RECORDED_NOT_MODELLED", "prescription for home; not a dose given here"),
    "conditional": ("RECORDED_NOT_MODELLED", "conditional plan recorded; the simulator does not carry it out"),
    "repeat": ("RECORDED_NOT_MODELLED", "repeat instruction recorded; the simulator does not carry it out"),
    "future_timed": ("RECORDED_NOT_MODELLED",
                     "timed order for later recorded; timed execution is not supported in this pilot"),
}


def plan_orders(parsed, *, submission_id, minute, start=2000):
    """Orders the reader recorded rather than ran: unmodelled decisions, plans, timed orders."""
    out = []
    details = list(parsed.get("future_details") or []) + list(parsed.get("ledger_plans") or [])
    for offset, detail in enumerate(details):
        if not isinstance(detail, dict) or detail.get("kind") not in _PLAN_KINDS:
            # Advice to the patient and treatment received before the resident's care are
            # not orders of this encounter.
            continue
        fate, reason = _PLAN_KINDS[detail["kind"]]
        order = {
            "order_id": detail.get("_order_id") or f"{submission_id}:p{start + offset}",
            "submission_id": submission_id,
            "span": str(detail.get("text") or ""),
            "canonical": f"plan:{detail['kind']}" + (f":{detail['category']}" if detail.get("category") else ""),
            "class": "not_modelled" if detail["kind"] in ("not_modelled", "prescription") else "plan",
            "dose": None, "route": None, "rate": None,
            "timing": ({"in_min": detail.get("in_min")} if detail.get("in_min") is not None else None),
            "written_at_min": minute, "fate": None, "reason": None, "executed_at_min": None,
            "receipt": None, "modelled_effect": False, "history": [],
        }
        if detail["kind"] == "future_timed":
            order["limitation"] = "unsupported_future_execution"
            order["receipt"] = detail.get("receipt")
        else:
            # The room already says these, by kind (unexecuted_items).
            order["receipt_shown_elsewhere"] = True
        set_fate(order, fate, reason, minute=minute)
        out.append(order)
    return out


def receipt_lines(orders):
    """What the room says about every order that did not simply run, one line each."""
    lines = []
    for order in orders:
        if order.get("receipt_shown_elsewhere"):
            continue
        if order.get("fate") == "EXECUTED" and not order.get("default_applied"):
            continue
        if order.get("receipt"):
            lines.append(order["receipt"])
    return list(dict.fromkeys(lines))


def validate(orders, cov=None):
    """Problems that must make a turn fail: an order without a valid fate, a span unaccounted."""
    problems = []
    for order in orders:
        if order.get("fate") not in FATES:
            problems.append(f"order {order.get('order_id')} has no valid fate: {order.get('fate')!r}")
    if cov is not None:
        spans = {fold(order.get("span") or "") for order in orders}
        for item in cov.get("unaccounted") or []:
            if fold(item["text"]) not in spans:
                problems.append(f"actionable text without a fate: {item['text']!r}")
    return problems


def snapshot(orders):
    """The orders as the Trace keeps them (no internal fields)."""
    keep = ("order_id", "submission_id", "span", "canonical", "class", "dose", "route", "rate", "timing",
            "written_at_min", "fate", "reason", "executed_at_min", "receipt", "modelled_effect", "history",
            "limitation", "detected_as", "default_applied", "group")
    return [{key: deepcopy(order.get(key)) for key in keep if key in order} for order in orders]
