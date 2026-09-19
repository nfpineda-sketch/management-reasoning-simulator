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
    "beta_blocker", "diltiazem", "amiodarone", "procedural_sedation", "cardioversion", "ventilator_adjustment", "steroid", "dextrose", "naloxone", "blood", "ppi", "aspirin", "nitroglycerin_bolus",
    "anticoagulation", "bag_mask", "intubation", "norepinephrine", "dobutamine", "diuretic",
    "magnesium",
})

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
    "naloxone": {"naloxone": r"naloxone|naloxona|narcan"},
    "ppi": {"pantoprazole": r"pantoprazole|pantoprazol", "omeprazole": r"omeprazole|omeprazol"},
    "aspirin": {"aspirin": r"aspirin|aspirina|asa|aas"},
    "anticoagulation": {"heparin": r"heparin|heparina", "enoxaparin": r"enoxaparin|enoxaparina"},
    "beta_blocker": {"metoprolol": r"metoprolol", "propranolol": r"propranolol"},
    "diltiazem": {"diltiazem": r"diltiazem|dilt"},
    "amiodarone": {"amiodarone": r"amiodarone|amiodarona|amio"},
    "procedural_sedation": {
        "etomidate": r"etomidate|etomidato", "midazolam": r"midazolam",
        "ketamine": r"ketamine|ketamina", "propofol": r"propofol", "fentanyl": r"fentanyl|fentanilo",
    },
    "diuretic": {"furosemide": r"furosemide|furosemida|lasix"},
}
_DIAGNOSTICS = {
    "head_ct": r"head ct|ct head|brain ct|ct brain|tac(?:\s+de)?\s+cerebro|tc(?:\s+de)?\s+cerebro|tomografia(?:\s+de)?\s+cerebro",
    "abdominal_ct": r"abdominal ct|ct abdomen|ct of the abdomen|tac(?:\s+de)?\s+abdomen|tc(?:\s+de)?\s+abdomen",
    "cortisol": r"cortisol",
    "thyroid_function": r"thyroid function|thyroid tests|tsh|perfil tiroideo|funcion tiroidea",
    "ketones": r"ketones|beta[- ]hydroxybutyrate|cetonas|cetonemia|beta[- ]hidroxibutirato",
    "toxicology": r"toxicology|toxicology screen|toxicologia|screening toxicologico",
    "pocus": r"pocus|point[- ]of[- ]care ultrasound|bedside ultrasound|ecografia(?:\s+a pie de cama)?|ultrasonido",
    "lactate": r"lactate|lactato",
    "vbg": r"vbg|venous blood gases?|venous blood gas|gasometria venosa|gases venosos",
    "abg": r"abg|arterial blood gases?|arterial blood gas|gasometria arterial|gases arteriales",
    "basic_labs": r"basic labs|blood tests|blood work|laboratory tests|laboratorio|examenes de laboratorio|hemograma|cbc|bmp|cmp|electrolytes|electrolitos|creatinine|creatinina",
    "temperature": r"temperature|temperatura|temp",
    "poc_glucose": r"poc glucose|blood glucose|blood sugar|fingerstick|finger stick|glucose|glucosa|glicemia|glucemia|hgt|hemoglucotest",
    "chest_xray": r"chest x[- ]?ray|chest radiograph|cxr|radiografia de torax|rx(?:\s+de)?\s+torax",
    "urinalysis": r"urinalysis|urine analysis|urine dip|orina completa|examen de orina",
    "blood_cultures": r"blood cultures?|hemocultivos?",
    "troponin": r"troponin|troponina",
    "ctpa": r"ctpa|ct pulmonary angiogra(?:phy|m)|pulmonary ct angiogra(?:phy|m)|angio(?:[- ]?tc|tac)(?:\s+(?:de\s+)?(?:torax|pulmonar))?",
    "hemoglobin": r"hemoglobin|hemoglobina|hb",
    "ecg": r"(?:12[- ](?:lead|derivadas?)\s+)?ecg(?:\s+(?:de\s+)?12\s+derivadas?)?|ekg|electrocardiogram|electrocardiograma",
}
# An airway/ventilation order and the settings fragments that may follow it.
_VENTILATION_ORDER = re.compile(
    r"\b(?:intubate|intubar|intuba|intubacion|intubación|rsi|rapid sequence|bipap|cpap|niv|vni|"
    r"ventilator|ventilation|ventilacion|ventilación|vc/ac|pc/ac|ac/vc|psv)\b", re.I)
_VENTILATION_SETTING = re.compile(
    r"^(?:at\s+|with\s+|a\s+|con\s+|de\s+)?(?:fio2|fio₂|peep|ipap|epap|tidal\s+volume|vt|"
    r"volumen\s+corriente|respiratory\s+rate|rate|frecuencia|i\s*:\s*e|mode|modo|vc/ac|pc/ac|ac/vc|psv|"
    r"pressure\s+support|presion\s+soporte|presión\s+soporte)\b", re.I)

_COMMAND = re.compile(
    r"^(?:(?:i\s+(?:will|want to)|i'll|i am going to|voy a|quiero|vamos a)\s+)?"
    r"(?P<verb>monitor|assess|vigilar|monitorizar|repeat|repetir|repito|repite|cardiovert|cardiovertir|cardiovierto|give|want|administer|apply|start|initiate|infuse|bolus|order|request|obtain|check|measure|send|get|perform|do|"
    r"stop|discontinue|increase|decrease|titrate|continue|change|set|switch|adjust|modify|reduce|wean|transfuse|nebulize|"
    r"consult|call|activate|admit|transfer|intubate|ventilate|reassess|re-assess|recheck|reevaluate|"
    r"administrar|administro|administre|aplicar|aplico|colocar|coloco|poner|pongo|dar|doy|iniciar|inicio|inicie|infundir|indicar|indico|"
    r"solicitar|solicito|solicite|pedir|pido|medir|mido|controlar|control|obtener|realizar|hacer|"
    r"suspender|suspendo|detener|aumentar|aumento|disminuir|disminuyo|titular|continuar|mantener|"
    r"ajustar|cambiar|transfundir|transfundo|nebulizar|consultar|interconsultar|llamar|activar|"
    r"hospitalizar|ingresar|trasladar|intubar|intubo|ventilar|reevaluar|reevaluo|revalorar)\b\s*"
)
# Spanish orders are written in the infinitive ("iniciar"), the tu imperative
# ("inicia") or the usted imperative ("inicie"). The verb sets below list one
# form per verb, so a clause-initial imperative is read as its infinitive first.
_ES_IMPERATIVES = {
    "iniciar": "inicia comienza comience empieza empiece comenzar empezar",
    "administrar": "administra", "dar": "da", "poner": "pon ponga", "colocar": "coloca coloque",
    "aplicar": "aplica aplique", "infundir": "infunde infunda", "indicar": "indica",
    "pedir": "pide pida", "solicitar": "solicita", "medir": "mide mida",
    "controlar": "controla controle", "obtener": "obten obtenga", "realizar": "realiza realice",
    "hacer": "haz haga", "suspender": "suspende suspenda", "detener": "deten detenga",
    "aumentar": "aumenta aumente", "disminuir": "disminuye disminuya", "titular": "titula titule",
    "continuar": "continua", "mantener": "manten mantenga", "ajustar": "ajusta ajuste",
    "cambiar": "cambia cambie", "transfundir": "transfunde transfunda", "nebulizar": "nebuliza nebulice",
    "consultar": "consulta", "interconsultar": "interconsulta interconsulte", "llamar": "llama llame", "activar": "activa active",
    "hospitalizar": "hospitaliza hospitalice", "ingresar": "ingresa ingrese",
    "trasladar": "traslada traslade", "intubar": "intuba intube", "ventilar": "ventila ventile",
    "reevaluar": "reevalua reevalue",
}
_ES_IMPERATIVE_FORMS = {form: verb for verb, forms in _ES_IMPERATIVES.items() for form in forms.split()}
_ES_IMPERATIVE = re.compile(
    r"(^|[.;\n,+:]\s*|\b(?:y|e(?=\s+h?i)|luego|and|then)\s+)(" + "|".join(sorted(_ES_IMPERATIVE_FORMS, key=len, reverse=True)) + r")\b"
)


_DIAG_VERBS = {
    "want", "order", "request", "obtain", "check", "measure", "send", "get", "perform", "do",
    "solicitar", "solicito", "solicite", "pedir", "pido", "medir", "mido", "controlar",
    "control", "obtener", "realizar", "hacer", "recheck",
}
_NON_ORDER = re.compile(
    r"\b(?:i think|i suspect|i believe|i expect|i anticipate|i hope|my hypothesis|my impression|"
    r"my working model|my working diagnosis|my priority|my plan|working diagnosis|because|need to improve|to improve|should improve|would improve|may improve|"
    r"pienso|creo|sospecho|espero|anticip[oae]|mi hipotesis|mi impresion|mi prioridad|mi plan|porque|para mejorar)\b"
)
_CONDITIONAL = re.compile(
    r"\b(?:if|unless|consider|considering|might|could|would|perhaps|maybe|si|salvo que|considerar|considero|podria|quizas|tal vez)\b"
)
_NEGATION = re.compile(r"^(?:please\s+)?(?:do not|don't|dont|never|avoid|no|not|sin|evitar|evito)\b")
_OXYGEN_DEVICES = (
    ("nasal cannula", r"nasal cann?ula|canula nasal|naricera|nasal prongs|nc"),
    ("non-rebreather mask", r"non[- ]rebreather(?: mask)?|non[- ]rebreathing mask|nrb|mascarilla(?:\s+con)?\s+reservorio"),
    ("simple mask", r"simple (?:face )?mask|mascarilla simple"),
    ("room air", r"room air|aire ambiente"),
)
_OXYGEN_MENTION = r"\b(?:oxygen|oxigeno|o2|nasal cann?ula|canula nasal|naricera|nasal prongs|nc|non[- ]rebreather|non[- ]rebreathing|nrb|simple mask|mascarilla|room air|aire ambiente)\b"
_FLOW = r"(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(?:l\s*/\s*(?:min|m)\b|lpm|lts?\s*/\s*min|(?:lts?|l)(?![\w/]|\s*/)|liters?\s*/\s*min|litres?\s*/\s*min|litros?\s*/\s*min)\b"




def _clarification(message):
    return {"type": "clarification", "message": message}






def _medication(text, kind, agent):
    dose, units = _amount(text, r"mcg|ug|mg|grams?|gramos?|g|units?|unidades|ui|u")
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
    if verb in {"stop", "discontinue", "suspender", "suspendo", "detener"}:
        return "stop"
    if verb in {"increase", "decrease", "titrate", "change", "set", "switch", "adjust", "modify", "reduce", "wean", "aumentar", "aumento", "disminuir", "disminuyo", "titular", "ajustar", "cambiar"}:
        return "adjust"
    if verb in {"continue", "continuar", "mantener"}:
        return "continue"
    return "start"


def _settings(text, name):
    if name == "fio2" and not re.search(r"\bfio2\b", text):
        # O2 expressed as a percentage is a respiratory setting, not a flow.
        text = re.sub(r"\bo2(?=\s*(?:of|de|=|at|to|a)?\s*[-.\d]+\s*%)", "fio2", text)
    match = re.search(r"\b" + name + r"\s*(?:of|de|=|at|to|a)?\s*(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(%)?", text)
    if not match:
        return None
    value = float(match[1])
    # FiO2 can be explicitly written as a fraction or percentage.
    return value * 100 if name == "fio2" and 0 < value <= 1 and not match[2] else value


def _oxygen_order(body, verb):
    """Bind the device and flow to the explicit target, never the prior setting."""
    if _operation(verb) == "stop":
        return {"type": "oxygen", "device": "room air", "flow_lpm": 0}
    if re.search(r"\b(?:high[- ]flow|hfnc|alto flujo)\b", body):
        return _clarification("High-flow oxygen is not a supported device in this encounter. Specify an available oxygen device and flow.")
    if _operation(verb) == "adjust" and re.search(r"\b(?:by|en)\s+-?\d", body):
        return _clarification("Specify the absolute target oxygen flow in L/min, not a relative change.")

    def devices(segment):
        matches = [(match.start(), name) for name, pattern in _OXYGEN_DEVICES
                   for match in re.finditer(r"\b(?:" + pattern + r")\b", segment)]
        return [name for _, name in sorted(matches)]

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
        return {**_clarification("Specify one target oxygen device and its flow in L/min."),
                **({"pending_action": {"type": "oxygen", "device": None, "flow_lpm": float(re.search(_FLOW, target)[1]) if re.search(_FLOW, target) else None}} if not selected and verb not in {"switch", "cambiar"} and len(list(re.finditer(_FLOW, target))) <= 1 else {})}
    device = selected.pop() if selected else None
    if device == "room air":
        return {"type": "oxygen", "device": device, "flow_lpm": 0}
    flows = list(re.finditer(_FLOW, target))
    if len(flows) > 1 or (not flows and _operation(verb) not in {"adjust", "continue"}):
        return {**_clarification("Specify one absolute target oxygen flow in L/min."),
                **({"pending_action": {"type": "oxygen", "device": device, "flow_lpm": None}} if not flows else {})}
    return {"type": "oxygen", "device": device, "flow_lpm": float(flows[0][1]) if flows else None, **({"operation": _operation(verb)} if _operation(verb) in {"adjust", "continue"} and (device is None or not flows) else {})}


def _parse_piece_core(piece, inherited=None):
    if re.fullmatch(r"\s*(?:prepare|set up|get ready|preparar|prepara)(?:\s+(?:for|para))?\s+(?:intubation|intubacion|airway|via aerea)\s*[.!]?", piece):
        return [{"type": "airway_preparation"}], "prepare"
    text = piece.strip(" :")
    text = re.sub(r"^(?:please|por favor|then|luego|despues)\s+", "", text)
    command = _COMMAND.match(text)
    verb = command["verb"] if command else inherited
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
    if not body and verb not in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar", "intubate", "intubar", "intubo"}:
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
            if re.search(r"\b(?:saline|ns|sf|salino|suero fisiologico|solucion fisiologica)\b", body):
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

    diagnostics = []
    for diagnostic, pattern in _DIAGNOSTICS.items():
        match = re.search(r"\b(?:" + pattern + r")\b", body)
        if match and (verb in _DIAG_VERBS or re.fullmatch(r"\s*(?:" + pattern + r")\s*\??", body)):
            diagnostics.append((match.start(), {"type": "diagnostic", "diagnostic": diagnostic}))
    if diagnostics:
        return [action for _, action in sorted(diagnostics, key=lambda x: x[0])], verb or "order"
    if re.search(r"\b(?:gases|gasometria|blood gases?)\b", body):
        return [{'type': 'clarification', 'message': 'Specify arterial (ABG) or venous (VBG) blood gases.',
                 'pending_action': {'type': 'diagnostic', 'diagnostic': None}}], verb
    if verb in _DIAG_VERBS and verb not in {"order", "perform", "do", "realizar", "hacer"}:
        return [_clarification("The requested study was not recognized. Specify one supported study per order.")], verb

    if not verb:
        shorthand = r"(?:synchronized cardioversion|synchronized shock|choque sincronizado|cardioversion|bipap|cpap|niv|vni|intubation|intubacion|bag[- ]mask|bag[- ]valve[- ]mask|bvm|ambu|oxygen|oxigeno|o2|nasal cann?ula|canula nasal|naricera|nc|non[- ]rebreather|nrb|room air|aire ambiente|dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|nitroglycerin|nitroglicerina|nitro)"
        medication_start = any(re.match(r"(?:" + pattern + r")\b", body) for agents in _AGENTS.values() for pattern in agents.values())
        quantity_start = bool(re.match(r"-?\d+(?:\.\d+)?\s*(?:mcg|ug|mg|g|ml|cc|l|units?|unidades?)\b", body))
        if not (re.match(shorthand + r"\b", body) or medication_start or quantity_start):
            return [], None
        if re.search(r"\b(?:was|were|has been|had been|previously|already|caused|improved|worsened|fue|recibio|previamente|ya recibio|mejoro|empeoro)\b", body):
            return [], None

    medication_count = sum(bool(re.search(r"\b(?:" + pattern + r")\b", body)) for agents in _AGENTS.values() for pattern in agents.values())
    has_fluid = bool(re.search(r"\b(?:saline|ns|sf|ringer|ringers|lr|crystalloid|cristaloides?|salino|suero fisiologico|solucion fisiologica)\b", body))
    if medication_count > 1 or (medication_count and has_fluid):
        return [_clarification("Separate each medication or fluid with its own dose and route so the order is unambiguous.")], verb

    if re.search(r"\b(?:consult|call|consultar|interconsultar|llamar)\b", text) or verb in {"activate", "activar"}:
        service = None
        for name, pattern in (("PERT", r"\bpert\b"), ("cardiology", r"cardiolog"), ("cath lab", r"cath(?:eterization)? lab|hemodinamia|hemodinamica"), ("gastroenterology", r"gastroenterolog|endoscop"), ("ICU", r"\bicu\b|\buci\b|intensive care|cuidados intensivos")):
            if re.search(pattern, body):
                service = name
                break
        return [{"type": "consult", "service": service}], verb
    if verb in {"admit", "transfer", "hospitalizar", "ingresar", "trasladar"}:
        destination = "ICU" if re.search(r"\b(?:icu|uci)\b|intensive care|cuidados intensivos", body) else None
        if re.search(r"\bward\b|\bsala\b|hospital ward", body):
            destination = "ward"
        return [{"type": "disposition", "destination": destination}], verb
    if verb in {"cardiovert", "cardiovertir", "cardiovierto"} or re.search(r"\b(?:cardioversion|synchronized shock|choque sincronizado)\b", body):
        if re.search(r"\b(?:unsynchronized|defibrillation|no sincronizado)\b", body):
            return [_clarification("Specify synchronized cardioversion; defibrillation is outside this pulse-present encounter.")], verb
        energy, _ = _amount(body, r"j|joules?|julios?")
        return [{"type": "cardioversion", "energy_j": energy, "synchronized": True}], verb
    if (_operation(verb) in {"adjust", "continue"} and re.search(r"\b(?:ventilator|ventilation|fio2|peep|ipap|epap|vc[/ -]?ac|pc[/ -]?ac)\b", body)
            and not re.search(r"\b(?:bipap|cpap|niv|vni)\b", body)):
        if re.search(r"\b(?:by|en)\s+-?\d", body):
            return [_clarification("Specify absolute target ventilator settings, not a relative change.")], verb
        modes = [mode for mode, pattern in (("VC/AC", r"\bvc[/ -]?ac\b|volume control"), ("PC/AC", r"\bpc[/ -]?ac\b|pressure control")) if re.search(pattern, body)]
        if len(modes) > 1:
            return [_clarification("Specify one target ventilator mode.")], verb
        return [{"type": "respiratory_adjustment", "operation": _operation(verb),
                 "ventilator_mode": modes[0] if modes else None,
                 "fio2_percent": _settings(body, "fio2"), "peep_cmh2o": _settings(body, "peep"),
                 "ipap_cmh2o": _settings(body, "ipap"), "epap_cmh2o": _settings(body, "epap")}], verb
    if re.search(r"\b(?:bag[- ]mask|bag[- ]valve[- ]mask|bvm|ambu|bolsa[- ]mascarilla|bolsa valvula mascarilla)\b", body):
        return [{"type": "bag_mask"}], verb
    if verb in {"intubate", "intubar", "intubo"} or re.match(r"(?:intubation|intubacion)\b", body):
        mode = "VC/AC" if re.search(r"\bvc[/ -]?ac\b|volume control|control volumen", body) else None
        if re.search(r"\bpc[/ -]?ac\b|pressure control|control presion", body):
            mode = "PC/AC"
        return [{"type": "intubation", "ventilator_mode": mode, "fio2_percent": _settings(body, "fio2"), "peep_cmh2o": _settings(body, "peep")}], verb
    if re.search(r"\b(?:bipap|cpap|niv|vni|non[- ]invasive ventilation|ventilacion no invasiva)\b", body):
        mode = "CPAP" if re.search(r"\bcpap\b", body) else "BiPAP" if re.search(r"\bbipap\b", body) else None
        ipap, epap = _settings(body, "ipap"), _settings(body, "epap")
        pair = re.search(r"\bbipap\s+(?:at\s+|a\s+)?(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", body)
        if pair and ipap is None and epap is None:
            ipap, epap = float(pair[1]), float(pair[2])
        cpap = re.search(r"\bcpap\s+(?:at\s+|a\s+)?(\d+(?:\.\d+)?)", body)
        if cpap and epap is None:
            epap = float(cpap[1])
        return [{"type": "niv", "mode": mode, "ipap_cmh2o": ipap, "epap_cmh2o": epap, "fio2_percent": _settings(body, "fio2"), "operation": _operation(verb)}], verb
    if re.search(r"\b(?:dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro)\b", body):
        kind = "nitroglycerin" if re.search(r"\b(?:nitroglycerin|nitroglicerina|nitro)\b", body) else "dobutamine" if re.search(r"\b(?:dobutamine|dobutamina)\b", body) else "norepinephrine"
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
        name = {"nitroglycerin": "Nitroglycerin", "dobutamine": "Dobutamine"}.get(kind, "Norepinephrine")
        single_dose = re.search(
            r"\b(?:bolus|bolo|push|stat\s+dose|sublingual|sublingual|sl|spray|tablet|tableta|comprimido|"
            r"pastilla|dosis\s+unica|dosis\s+única)\b", body)
        mass_dose = None if rate_match else re.search(
            r"(?<![\w.])((?:\d+(?:\.\d+)?|\.\d+))\s*(mcg|ug|mg)\b(?!\s*/)", body)
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
    if re.search(r"\b(?:saline|normal saline|ns|sf|sf|ringer|lactated ringers?|lr|crystalloid|cristaloides?|salino|suero fisiologico|solucion fisiologica|sueros?|fluid|fluids|volumen)\b", body):
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
        if re.search(r"\b(?:saline|ns|sf|salino|suero fisiologico|solucion fisiologica)\b", body):
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
            if _operation(verb) != "start":
                return [_clarification("This fixed-dose medication order needs an explicit new dose; stopping or continuing it is not a supported new administration.")], verb
            medication_text = body + " nebulized" if verb in {"nebulize", "nebulizar"} else body
            return [_medication(medication_text, kind, agent)], verb or "give"
    if verb:
        # Quote the fragment back: a resident cannot repair an unnamed item, and
        # the rest of the submission is held rather than discarded.
        fragment = " ".join(str(piece).split())[:80]
        return [{**_clarification(
            f'This order was not recognized: "{fragment}". Replace it with a supported '
            "intervention, dose/settings and route, or say cancel. The other orders in "
            "this submission are held until then."), "unrecognized_text": fragment}], verb
    return [], None


def _parse_piece(piece, inherited=None):
    dose_piece = re.sub(r"\b(?:over|durante|en)\s+\d+(?:\.\d+)?\s*(?:minutes?|mins?|minutos?|hours?|horas?|seconds?|segundos?)\b", "", piece)
    if re.search(r"\b(?:reassess|reevaluar|reevaluo|revalorar|reassessment)\b", piece):
        dose_piece = piece
    actions, verb = _parse_piece_core(dose_piece, inherited)
    # Delivery time is attached to this treatment clause, never to reasoning or
    # the reassessment clause. Retain unsupported/ambiguous timing as a question.
    text = _NON_ORDER.split(piece, maxsplit=1)[0]
    matches = list(re.finditer(r"\b(?:over|durante|en)\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|minutos?|hours?|horas?|seconds?|segundos?)\b", text))
    treatments = [a for a in actions if a['type'] not in {'diagnostic', 'reassessment', 'clarification'}]
    if matches and treatments:
        if len(matches) != 1 or len(treatments) != 1:
            return [_clarification("Specify one delivery duration for each treatment.")], verb
        value, unit = float(matches[0][1]), matches[0][2]
        value *= 60 if unit.startswith(('hour', 'hora')) else 1 / 60 if unit.startswith(('second', 'segundo')) else 1
        treatments[0]['administration_duration_min'] = value
    return actions, verb


# Verbs that also state a goal: "and increase perfusion" is reasoning, whereas
# "and increase FiO2 to 80%" is an order.
_GOAL_VERBS = {"increase", "decrease", "titrate", "continue", "aumentar", "aumento",
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
        first = re.split(r"\s*(?:,|\+|\band\b|\by\b|\be\b(?=\s+h?i)|\bthen\b|\bluego\b)\s*", rest, maxsplit=1)[0]
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
    normalized = _ES_IMPERATIVE.sub(lambda m: m.group(1) + _ES_IMPERATIVE_FORMS[m.group(2)], _normalize(raw))
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
            if boundary:
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
        # Do not split the clinical device name "bag and mask".
        sentence = re.sub(r"\bbag and mask\b", "bag-mask", sentence)
        pieces = re.split(r"\s*(?:,|\+|\band\b|\by\b|\be\b(?=\s+h?i)|\bthen\b|\bluego\b)\s*", sentence)
        # Ventilator settings written naturally ("intubate, VC/AC, FiO2 100% and
        # PEEP 5") belong to the airway order, not to separate orders.
        merged = []
        for piece in pieces:
            if merged and _VENTILATION_SETTING.match(piece) and _VENTILATION_ORDER.search(merged[-1]):
                merged[-1] += " " + piece
            else:
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
                inherited = None
                continue
            parsed, inherited = _parse_piece(piece, inherited)
            actions.extend(parsed)
    return {"raw_text": raw, "actions": actions, "recognized_future_actions": future}
