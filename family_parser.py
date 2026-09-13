"""Small, deterministic order interpreter for the independent case families.

The parser identifies orders; the family engine validates whether they can be
executed.  It does not infer doses, routes, clinical reasoning, or treatment from
a diagnosis/expected effect.  Unrecognized explicit orders remain visible as
clarifications instead of being reported as successful interventions.
"""
from __future__ import annotations

import re
import unicodedata


NEW_TREATMENT_ACTIONS = frozenset({
    "fluid", "oxygen", "niv", "nitroglycerin", "antibiotics", "bronchodilator",
    "steroid", "dextrose", "naloxone", "blood", "ppi", "aspirin",
    "anticoagulation", "bag_mask", "intubation", "norepinephrine", "diuretic",
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
    "naloxone": {"naloxone": r"naloxone|naloxona|narcan"},
    "ppi": {"pantoprazole": r"pantoprazole|pantoprazol", "omeprazole": r"omeprazole|omeprazol"},
    "aspirin": {"aspirin": r"aspirin|aspirina|asa|aas"},
    "anticoagulation": {"heparin": r"heparin|heparina", "enoxaparin": r"enoxaparin|enoxaparina"},
    "diuretic": {"furosemide": r"furosemide|furosemida|lasix"},
}
_DIAGNOSTICS = {
    "pocus": r"pocus|point[- ]of[- ]care ultrasound|bedside ultrasound|ecografia(?:\s+a pie de cama)?|ultrasonido",
    "lactate": r"lactate|lactato",
    "vbg": r"vbg|venous blood gas|gasometria venosa|gases venosos",
    "abg": r"abg|arterial blood gas|gasometria arterial|gases arteriales",
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
_COMMAND = re.compile(
    r"^(?:(?:i\s+(?:will|want to)|i'll|i am going to|voy a|quiero|vamos a)\s+)?"
    r"(?P<verb>give|administer|apply|start|initiate|infuse|bolus|order|request|obtain|check|measure|send|get|perform|do|"
    r"stop|discontinue|increase|decrease|titrate|continue|change|set|switch|transfuse|nebulize|"
    r"consult|call|activate|admit|transfer|intubate|ventilate|reassess|re-assess|recheck|reevaluate|"
    r"administrar|administro|administre|aplicar|aplico|colocar|coloco|poner|pongo|dar|doy|iniciar|inicio|inicie|infundir|indicar|indico|"
    r"solicitar|solicito|solicite|pedir|pido|medir|mido|controlar|control|obtener|realizar|hacer|"
    r"suspender|suspendo|detener|aumentar|aumento|disminuir|disminuyo|titular|continuar|mantener|"
    r"ajustar|cambiar|transfundir|transfundo|nebulizar|consultar|interconsultar|llamar|activar|"
    r"hospitalizar|ingresar|trasladar|intubar|intubo|ventilar|reevaluar|reevaluo|revalorar)\b\s*"
)
_DIAG_VERBS = {
    "order", "request", "obtain", "check", "measure", "send", "get", "perform", "do",
    "solicitar", "solicito", "solicite", "pedir", "pido", "medir", "mido", "controlar",
    "control", "obtener", "realizar", "hacer", "recheck",
}
_NON_ORDER = re.compile(
    r"\b(?:i think|i suspect|i believe|i expect|i anticipate|i hope|my hypothesis|my impression|"
    r"my working model|my working diagnosis|my priority|my plan|working diagnosis|because|to improve|should improve|would improve|may improve|"
    r"pienso|creo|sospecho|espero|anticip[oae]|mi hipotesis|mi impresion|mi prioridad|mi plan|porque|para mejorar)\b"
)
_CONDITIONAL = re.compile(
    r"\b(?:if|unless|consider|considering|might|could|would|perhaps|maybe|si|salvo que|considerar|considero|podria|quizas|tal vez)\b"
)
_NEGATION = re.compile(r"^(?:please\s+)?(?:do not|don't|dont|never|avoid|no|not|sin|evitar|evito)\b")
_OXYGEN_DEVICES = (
    ("nasal cannula", r"nasal cannula|canula nasal|naricera|nasal prongs|nc"),
    ("non-rebreather mask", r"non[- ]rebreather(?: mask)?|non[- ]rebreathing mask|nrb|mascarilla(?:\s+con)?\s+reservorio"),
    ("simple mask", r"simple (?:face )?mask|mascarilla simple"),
    ("room air", r"room air|aire ambiente"),
)
_OXYGEN_MENTION = r"\b(?:oxygen|oxigeno|o2|nasal cannula|canula nasal|naricera|nasal prongs|nc|non[- ]rebreather|non[- ]rebreathing|nrb|simple mask|mascarilla|room air|aire ambiente)\b"
_FLOW = r"(-?\d+(?:\.\d+)?)\s*(?:l\s*/\s*min|lpm|liters?\s*/\s*min|litres?\s*/\s*min|litros?\s*/\s*min)\b"


def _normalize(text):
    text = unicodedata.normalize("NFKD", str(text or "").replace("µ", "u").replace("μ", "u"))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("’", "'")
    # A decimal comma is numeric, whereas a comma separating orders is not.
    return re.sub(r"(?<=\d),(?=\d)", ".", text)


def _clarification(message):
    return {"type": "clarification", "message": message}


def _route(text):
    found = []
    for route, pattern in (
        ("IV", r"\b(?:iv|ev|intravenous|intravenously|intravenos[ao])\b"),
        ("IO", r"\b(?:io|intraosseous|intraose[ao])\b"),
        ("IM", r"\b(?:im|intramuscular)\b"),
        ("PO", r"\b(?:po|vo|oral|orally|por boca|por via oral)\b"),
        ("IN", r"\bintranasal\b|\bin\s*(?:now|ahora)?\s*$"),
        ("nebulized", r"\b(?:nebulized|nebulised|nebulization|nebulizado|nebulizada|nebulizar|nebulize|neb)\b"),
        ("inhaled", r"\b(?:inhaled|inhalado|inhalada)\b"),
        ("SC", r"\b(?:sc|sq|subcutaneous|subcutane[ao])\b"),
    ):
        if re.search(pattern, text):
            found.append(route)
    return found[0] if len(found) == 1 else None


def _amount(text, units):
    matches = list(re.finditer(r"(?<![\w.])(-?\d+(?:\.\d+)?)\s*(" + units + r")\b", text))
    if len(matches) != 1:
        return None, None
    return float(matches[0][1]), matches[0][2]


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
    if verb in {"increase", "decrease", "titrate", "change", "set", "switch", "aumentar", "aumento", "disminuir", "disminuyo", "titular", "ajustar", "cambiar"}:
        return "adjust"
    if verb in {"continue", "continuar", "mantener"}:
        return "continue"
    return "start"


def _settings(text, name):
    match = re.search(r"\b" + name + r"\s*(?:of|de|=|at|a)?\s*(-?\d+(?:\.\d+)?)\s*(%)?", text)
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
    if len(selected) != 1:
        return _clarification("Specify one target oxygen device and its flow in L/min.")
    device = selected.pop()
    if device == "room air":
        return {"type": "oxygen", "device": device, "flow_lpm": 0}
    flows = list(re.finditer(_FLOW, target))
    if len(flows) != 1:
        return _clarification("Specify one absolute target oxygen flow in L/min.")
    return {"type": "oxygen", "device": device, "flow_lpm": float(flows[0][1])}


def _parse_piece(piece, inherited=None):
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
    if not body and verb not in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar", "intubate", "intubar", "intubo"}:
        return [], verb

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
    if verb in _DIAG_VERBS and verb not in {"order", "perform", "do", "realizar", "hacer"}:
        return [_clarification("The requested study was not recognized. Specify one supported study per order.")], verb

    if not verb:
        shorthand = r"(?:bipap|cpap|niv|vni|intubation|intubacion|bag[- ]mask|bag[- ]valve[- ]mask|bvm|ambu|oxygen|oxigeno|o2|nasal cannula|canula nasal|naricera|nc|non[- ]rebreather|nrb|room air|aire ambiente|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|nitroglycerin|nitroglicerina|nitro)"
        medication_start = any(re.match(r"(?:" + pattern + r")\b", body) for agents in _AGENTS.values() for pattern in agents.values())
        quantity_start = bool(re.match(r"-?\d+(?:\.\d+)?\s*(?:mcg|ug|mg|g|ml|cc|l|units?|unidades?)\b", body))
        if not (re.match(shorthand + r"\b", body) or medication_start or quantity_start):
            return [], None
        if re.search(r"\b(?:was|were|has been|had been|previously|already|caused|improved|worsened|fue|recibio|previamente|ya recibio|mejoro|empeoro)\b", body):
            return [], None

    medication_count = sum(bool(re.search(r"\b(?:" + pattern + r")\b", body)) for agents in _AGENTS.values() for pattern in agents.values())
    has_fluid = bool(re.search(r"\b(?:saline|ns|ringer|ringers|lr|crystalloid|cristaloides?|salino|suero fisiologico|solucion fisiologica)\b", body))
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
    if re.search(r"\b(?:norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro)\b", body):
        kind = "nitroglycerin" if re.search(r"\b(?:nitroglycerin|nitroglicerina|nitro)\b", body) else "norepinephrine"
        rate_matches = list(re.finditer(r"(-?\d+(?:\.\d+)?)\s*(mcg|ug|mg)\s*/\s*(kg\s*/\s*)?(min(?:ute)?|h(?:r|our)?)\b", body))
        if len(rate_matches) > 1 or (_operation(verb) == "adjust" and re.search(r"\b(?:by|en)\s+-?\d", body)):
            return [_clarification("Specify a single absolute target infusion rate; a relative change or several rates is ambiguous.")], verb
        rate_match = rate_matches[0] if rate_matches else None
        rate, units = None, None
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
    if re.search(r"\b(?:saline|normal saline|ns|ringer|lactated ringers?|lr|crystalloid|cristaloides?|salino|suero fisiologico|solucion fisiologica|fluid|fluids|volumen)\b", body):
        volume, units = _amount(body, r"ml|cc|liters?|litres?|litros?|l")
        if volume is not None and units not in {"ml", "cc"}:
            volume *= 1000
        fluid_type = None
        if re.search(r"\b(?:saline|ns|salino|suero fisiologico|solucion fisiologica)\b", body):
            fluid_type = "normal saline"
        elif re.search(r"\b(?:ringer|ringers|lr)\b", body):
            fluid_type = "lactated Ringer's"
        elif re.search(r"\b(?:crystalloid|cristaloides?)\b", body):
            fluid_type = "crystalloid"
        return [{"type": "fluid", "volume_ml": volume, "fluid_type": fluid_type}], verb

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
        return [_clarification("This order was not recognized. Specify the intervention, dose/settings, and route explicitly.")], verb
    return [], None


def parse_family_actions(text) -> dict:
    """Return source-ordered action dictionaries without changing patient state.

    Semicolons, full stops, and newlines end conditional/negated scope. Commas,
    ``and``/``y`` and ``+`` can chain orders and inherit an explicit order verb.
    A conditional instruction is retained as a future plan, never executed now.
    """
    raw = str(text or "")
    normalized = _normalize(raw)
    actions, future = [], []
    for sentence in re.split(r"[;\n]+|(?<!\d)\.(?!\d)|(?<=\d)\.(?!\d)", normalized):
        sentence = sentence.strip()
        if not sentence:
            continue
        # A priority/expected-response sentence is a description of reasoning,
        # even when a later conjunction contains words such as "reassess".
        if _NON_ORDER.match(sentence):
            continue
        if _COMMAND.match(sentence):
            rationale = _NON_ORDER.search(sentence)
            if rationale:
                sentence = sentence[:rationale.start()].strip(" ,")
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
        pieces = re.split(r"\s*(?:,|\+|\band\b|\by\b|\bthen\b|\bluego\b)\s*", sentence)
        grouped = []
        index = 0
        while index < len(pieces):
            piece = pieces[index]
            command = _COMMAND.match(piece)
            if command and command["verb"] in {"reassess", "re-assess", "reevaluate", "reevaluar", "reevaluo", "revalorar"}:
                while index + 1 < len(pieces) and not (_COMMAND.match(pieces[index + 1]) or _NON_ORDER.match(pieces[index + 1]) or _NEGATION.match(pieces[index + 1])):
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
