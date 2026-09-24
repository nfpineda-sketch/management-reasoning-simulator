"""The findings a resident names, and whether they said what those findings meant.

Section 3 of the faculty specification of 2026-09-23. Inside the working model,
and never as a fifth category, the record should hold the cues the resident
actually expressed. The distinction that matters for assessment is not whether
a datum was on the monitor but what the resident did with it:

* **available** — the datum was on the monitor or in the history;
* **consulted** — the resident asked for it (this simulator records that only
  for the history, in ``history_review``; nothing records looking at a monitor);
* **mentioned** — the resident wrote it in their entry. This module.
* **linked** — the resident said that this finding supported or questioned their
  interpretation. Also this module.

Two rules decide everything here, and both are refusals:

* **Nothing is reconstructed from the intervention.** "Dar suero" names no
  finding, and hypovolaemia is not inferred from it. The lexicon matches words
  the resident wrote and cannot reach a word they did not.
* **A suspicion is not a fact and a prediction is not a present finding.**
  "Creo que está en shock" is an interpretation, not a cue; "espero que suba la
  presión" is an expectation, not an observation.

Linkage is operationalised as one explainable rule: a finding is linked when the
resident put it in the same statement as an explicit link marker ("porque", "me
preocupa que", "lo que sugiere", "because", "which suggests"). That is a claim
about what they wrote, not about what they thought, and the supporting text is
kept so a reader can disagree with it.
"""

from __future__ import annotations

import re


#: Findings written as a clinical word. Stems where a language inflects.
_NAMED_FINDINGS = (
    # perfusion and pressure
    r"hipotens\w*|hypotens\w*|hipertens\w*|hypertens\w*|shock[ae]d|chocad[oa]|"
    r"mal\s+perfundid[oa]|hipoperfundid[oa]|poorly\s+perfused|hypoperfused|"
    r"llene\s+capilar\s+(?:lento|prolongado|enlentecido)|"
    r"(?:delayed|prolonged|slow)\s+capillary\s+refill|"
    r"moteado|livedo|mottled|fri[oa]s?|cold\s+(?:extremities|peripheries)|"
    r"pulsos?\s+(?:d[eé]biles|filiformes)|weak\s+pulses|thready\s+pulse|"
    # rate and rhythm
    r"taquic[aá]rdic[oa]|tachycardic|bradic[aá]rdic[oa]|bradycardic|"
    r"taquiarritmia|fibrilaci[oó]n\s+auricular|atrial\s+fibrillation|a-?fib\b|"
    r"irregular\w*|supradesnivel\w*|infradesnivel\w*|st\s+elevation|st\s+depression|"
    r"ondas?\s+q|q\s+waves?|bloqueo\s+de\s+rama|bundle\s+branch\s+block|"
    # breathing and oxygenation
    r"hipox\w*|hypox\w*|desatura\w*|desaturat\w*|"
    r"taquipneic[oa]|tachypneic|tachypnoeic|disnea|disneic[oa]|dyspnea|dyspnoea|"
    r"dyspneic|short\s+of\s+breath|polipnea|"
    r"crepitantes?|crepitaciones|crackles|rales|estertores|"
    r"sibilancias|wheez\w*|roncus|rhonchi|"
    r"uso\s+de\s+(?:la\s+)?musculatura\s+accesoria|accessory\s+muscle\w*|"
    r"tiraje|retracciones|retractions|"
    r"trabajo\s+respiratorio\s+(?:aumentado|alto|elevado)|"
    r"(?:increased|high)\s+work\s+of\s+breathing|"
    r"murmullo\s+(?:pulmonar\s+)?(?:disminuido|abolido)|"
    r"(?:decreased|absent)\s+breath\s+sounds|"
    # neurology
    r"confus[oa]|confused|desorientad[oa]|disoriented|somnolient[oa]|somnolent|"
    r"obnubilad[oa]|sopor(?:os[oa])?|letárgic[oa]|lethargic|agitad[oa]|agitated|"
    r"comprometido\s+de\s+conciencia|alterad[oa]\s+de\s+conciencia|"
    r"altered\s+mental\s+status|encefalop[aá]tic[oa]|encephalopathic|glasgow|gcs\b|"
    r"focalidad|focal\s+deficit|convulsi\w*|seizure\w*|"
    # congestion and volume
    r"ingurgitaci[oó]n\s+yugular|yugulares?\s+ingurgitadas?|"
    r"(?:raised|elevated|distended)\s+jvp|jvd\b|jugular\s+venous\s+distension|"
    # "Edema pulmonar" is the name of a condition and belongs to the working
    # model; "edema" on its own, or of the legs, is something the resident saw.
    r"(?<!pulmonary )(?<!flash )edema(?!\s*(?:agudo|pulmonar|de\s+pulm[oó]n))\w*|"
    r"(?<!pulmonary )(?<!flash )oedema\w*|congesti[oó]n|congested|congestion|"
    r"reflujo\s+hepatoyugular|hepatojugular\s+reflux|ortopnea|orthopnea|"
    r"deshidratad[oa]|dehydrated|seco[as]?\s+mucosas|dry\s+mucous\s+membranes|"
    # skin, temperature, general
    r"sudoros[oa]|diaforétic[oa]|diaphoretic|sweaty|clammy|"
    r"p[aá]lid[oa]|pale|pallor|cian[oó]tic[oa]|cyanotic|cianosis|cyanosis|"
    r"ictéric[oa]|jaundiced|febril|febrile|afebril|afebrile|fiebre|fever|"
    r"hipot[eé]rmic[oa]|hypothermic|"
    # output and labs
    r"oligúric[oa]|oliguric|anúric[oa]|anuric|oliguria|anuria|"
    r"lactato\s+(?:alto|elevado)|(?:high|raised|elevated)\s+lactate|"
    r"acidosis|acid[oó]tic[oa]|acidotic|alcalosis|alkalosis|"
    r"hiperkalemia|hyperkalemia|hipoglic\w*|hypoglyc\w*|hiperglic\w*|hyperglyc\w*|"
    r"anemi[ac][oa]?|an[ae]mic|leucocitosis|leukocytosis|"
    r"troponina\s+(?:alta|elevada|positiva)|(?:raised|elevated)\s+troponin|"
    # what a sample or a surface looks like. Added 2026-09-23 after a paid
    # measurement: the model read "orina turbia" and the lexicon could not,
    # because the lexicon is closed. This closes part of that gap without
    # pretending the rest of it is closed.
    r"orina\s+(?:turbia|concentrada|oscura|hemat[uú]rica|f[eé]tida)|"
    r"(?:cloudy|dark|concentrated|foul[- ]smelling)\s+urine|"
    r"esputo\s+(?:purulento|hem[oá]ptico|herrumbroso)|purulent\s+sputum|"
    r"herida\s+(?:infectada|purulenta)|celulitis|cellulitis|"
    r"eritema|erythema|exantema|rash|petequias|petechiae|p[uú]rpura|purpura|"
    # symptoms
    r"dolor\s+(?:tor[aá]cico|precordial|abdominal|retroesternal)|"
    r"chest\s+pain|abdominal\s+pain|palpitaciones|palpitations|"
    r"v[oó]mitos?|vomiting|diarrea|diarrh[oe]a|"
    # syndromic words the resident uses as an observation
    r"sangrando|bleeding|hemorragia|h[ae]morrhage|"
    r"broncoespasmo|bronchospasm|sibilante"
)

#: A vital or a laboratory value written with its number. "PA 80/50", "sat 85%".
_MEASURED_FINDING = re.compile(
    r"\b(?:pa|pas|pad|pam|ta\b|bp|map|sbp|dbp|fc|hr|fr|rr|sat(?:uraci[oó]n)?|spo2|"
    r"temperatura|temp|t[ºo°]?|hgt|glicemia|glucosa|glucose|lactato|lactate|ph\b|"
    r"pco2|po2|paco2|pao2|hb|hemoglobina|h[ae]moglobin|gcs|glasgow|diuresis|"
    # "en" is missing on purpose: in Spanish it is the preposition of time, and
    # with it "reevaluo PAM en 10 minutos" was filed as a measurement of 10.
    r"urine\s+output)\b\s*(?:(?:is|es|est[aá]|was|de|of)\s+|[:=]\s*)?"
    r"(?:[<>]=?\s*)?\d+(?:[.,]\d+)?(?:\s*/\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:%|mmhg|lpm|bpm|x'|/min|mg/dl|mmol/l|mg|g/dl|ml(?:/h)?|[ºo°]c)?"
    # A number followed by a unit of time is an interval, not a value.
    r"(?!\s*(?:min\b|mins?\b|minutos?|minutes?|h\b|hr\b|horas?|hours?))",
    re.I)

_FINDING = re.compile(r"(?<![a-záéíóúñ])(?:" + _NAMED_FINDINGS + r")", re.I)

#: What the resident watches, named without a number. On its own that is not a
#: finding — "reevaluo la presion" says nothing about the patient — but beside a
#: word of change it is one: "la presion mejoro", "sigue confuso", "ya no
#: desatura". Section 3 asks for the change and the persistence to be kept.
_VARIABLE = (r"presi[oó]n(?:\s+arterial)?|pa\b|pam\b|pas\b|ta\b|bp\b|map\b|"
             r"frecuencia(?:\s+card[ií]aca|\s+respiratoria)?|fc\b|hr\b|fr\b|rr\b|"
             r"saturaci[oó]n|sat\b|spo2|oxigenaci[oó]n|oxygenation|saturation|"
             r"diuresis|d[eé]bito\s+urinario|urine\s+output|lactato|lactate|"
             r"temperatura|temperature|conciencia|mental\s+status|perfusi[oó]n|perfusion|"
             r"glicemia|glucemia|hgt|glucose|ritmo|rhythm|llene\s+capilar|"
             r"capillary\s+refill|trabajo\s+respiratorio|work\s+of\s+breathing|"
             r"dolor|pain|disnea|dyspnea|dyspnoea")

_TREND_WORD = (r"mejor[oó]|mejorando|mejor[ií]a|empeor[oó]|empeorando|subi[oó]|"
               r"baj[oó]|cay[oó]|aument[oó]|disminuy[oó]|"
               r"sigue|contin[uú]a|persiste|permanece|ya\s+no|"
               r"improved|improving|worsened|worsening|rose|fell|dropped|"
               r"increased|decreased|still|persists|remains|no\s+longer|continues")

_TRENDING_VARIABLE = re.compile(
    r"(?:(?:la|el|los|las|the)\s+)?(?:" + _VARIABLE + r")\s+(?:ya\s+)?(?:no\s+)?"
    r"(?:" + _TREND_WORD + r")\b"
    r"|(?:" + _TREND_WORD + r")\s+(?:(?:la|el|los|las|the)\s+)?(?:" + _VARIABLE + r")\b",
    re.I)

# The resident says this finding bears on their interpretation. Which side of
# the marker the evidence sits on depends on the marker: "porque" introduces the
# reason, "lo que sugiere" introduces the conclusion. Reading that backwards
# recorded the interpretation itself as a finding — "lo que sugiere congestion"
# was filed as an observation of congestion.
_LINK_EVIDENCE = (r"porque|debido\s+a(?:l)?|dado\s+que|ya\s+que|puesto\s+que|"
                  r"se\s+explica\s+por|a\s+partir\s+de|"
                  r"because|since|given\s+that|based\s+on|in\s+view\s+of")

_LINK_CONCLUSION = (r"me\s+preocupa\s+que|me\s+hace\s+pensar|lo\s+que\s+sugiere|"
                    r"esto\s+sugiere|sugiere[n]?|indica[n]?|orienta\s+a|apunta\s+a|"
                    r"compatible\s+con|concordante\s+con|por\s+eso|por\s+lo\s+que|"
                    r"as[ií]\s+que|impresiona|traduce|refleja[n]?|"
                    r"debe\s+ser|tiene\s+que\s+ser|"
                    r"which\s+suggests?|suggesting|this\s+suggests?|concerning\s+for|"
                    r"worried\s+(?:about|that)|makes\s+me\s+think|consistent\s+with|"
                    r"points?\s+to|so\s+i\s+(?:think|suspect)|in\s+keeping\s+with|"
                    r"indicates?|must\s+be")

_LINK = re.compile(r"\b(?:" + _LINK_EVIDENCE + r"|" + _LINK_CONCLUSION + r")\b", re.I)
_CONCLUSION_MARKER = re.compile(r"\b(?:" + _LINK_CONCLUSION + r")\b", re.I)

_ABSENT = re.compile(
    r"\b(?:sin|ni|no|niega|nega\w*|ausencia\s+de|ausente|without|nor|"
    r"no\s+evidence\s+of|denies|absent|free\s+of)\b", re.I)

_TREND = re.compile(
    r"\b(?:mejor[oó]|mejorando|empeor[oó]|empeorando|subi[oó]|baj[oó]|"
    r"sigue|contin[uú]a|persiste|persistente|permanece|ya\s+no|todav[ií]a|a[uú]n|"
    r"improved|improving|worsened|worsening|rose|fell|dropped|increased|decreased|"
    r"still|persists?|persistent|remains?|no\s+longer|continues)\b", re.I)

_UNCERTAIN = re.compile(
    r"\b(?:podr[ií]a|puede\s+(?:ser|estar)|quiz[aá]s?|tal\s+vez|posible\w*|"
    r"probable\w*|sospecho|impresiona|no\s+estoy\s+segur[oa]|dudo|"
    r"may\s+be|might|possibly|probably|likely|suspect|unclear|not\s+sure)\b", re.I)

_CONTRAST = re.compile(
    r"\b(?:pero|aunque|sin\s+embargo|no\s+obstante|en\s+cambio|"
    r"but|however|although|though|yet|whereas)\b", re.I)

#: A cue is what the resident observed. These say the opposite: an intention, an
#: expectation or a hypothesis, and a finding word inside one is not an
#: observation of it.
_NOT_AN_OBSERVATION = re.compile(
    r"\b(?:espero|anticipo|preveo|busco|quiero|apunto\s+a|la\s+idea\s+es|"
    r"para\s+(?:que\s+)?(?:no\s+)?\w+r\b|"
    r"i\s+expect|i\s+anticipate|expecting|the\s+goal\s+is|the\s+aim\s+is|"
    r"my\s+goal\s+is|aiming\s+(?:for|to)|hoping|in\s+order\s+to|so\s+that)\b",
    re.I)


def _statements(text):
    """Split on full stops and newlines only.

    A semicolon and a comma stay inside the statement: "Está hipotenso y
    confuso; me preocupa que esté en shock" is one thing the resident said, and
    splitting it would lose the link they wrote between the two halves.
    """
    for piece in re.split(r"(?<!\d)\.(?!\d)|\n+", str(text or "")):
        cleaned = piece.strip()
        if cleaned:
            yield cleaned


def _nearest(pattern, text):
    """Where the last match of ``pattern`` ends, or -1. Nearest wins."""
    last = -1
    for match in pattern.finditer(text):
        last = match.end()
    return last


def _polarity(statement, start):
    """How the resident held this finding: present, absent, changing, uncertain.

    When two markers are in front of the same finding the nearest one governs
    it. "La presion mejoro, pero sigue confuso, sin crepitantes ni fiebre" has a
    change marker and a negation in the same breath, and reading the first one
    printed absent findings as present ones (2026-09-24).
    """
    before = statement[max(0, start - 60):start]
    absent, trend = _nearest(_ABSENT, before), _nearest(_TREND, before)
    if absent > trend:
        return "absent"
    window = before + statement[start:start + 40]
    if trend >= 0 or _TREND.search(window):
        return "trend"
    if _UNCERTAIN.search(before):
        return "uncertain"
    return "present"


def cues(text):
    """The findings the resident wrote, in the order they wrote them.

    Each cue carries the span that supports it, so nothing here has to be taken
    on trust: a reader can see the resident's own words and decide whether the
    reading of them is fair.
    """
    found, seen = [], set()
    for statement in _statements(text):
        link = _LINK.search(statement)
        contrast = bool(_CONTRAST.search(statement))
        spans = [(m.start(), m.group(0)) for m in _FINDING.finditer(statement)]
        spans += [(m.start(), m.group(0)) for m in _MEASURED_FINDING.finditer(statement)]
        spans += [(m.start(), m.group(0)) for m in _TRENDING_VARIABLE.finditer(statement)]
        for start, span in sorted(spans):
            phrase = " ".join(str(span).split()).strip(" .,;:")
            if not phrase:
                continue
            # A finding word inside a wish is not an observation of it.
            clause_start = max(statement.rfind(",", 0, start), statement.rfind(";", 0, start)) + 1
            if _NOT_AN_OBSERVATION.search(statement[clause_start:start]):
                continue
            conclusion = _CONCLUSION_MARKER.search(statement[:start])
            if conclusion and not _LINK.search(statement[conclusion.end():start]):
                continue
            key = phrase.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "finding": phrase,
                "polarity": _polarity(statement, start),
                "linked": bool(link),
                "link_marker": link.group(0) if link else "",
                "contrast": contrast,
                "statement": " ".join(statement.split())[:300],
            })
    return found


def key(finding):
    """How two findings are compared, so the same one is never listed twice.

    Case, accents and run-together whitespace are transcription, not content:
    "Hipotenso" and "hipotenso" are one finding.
    """
    lowered = str(finding or "").lower()
    for source, target in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"),
                           ("ú", "u"), ("ü", "u"), ("ñ", "n")):
        lowered = lowered.replace(source, target)
    return re.sub(r"\s+", " ", lowered).strip(" .,;:")


def mentioned(text):
    """Just the findings, for a caller that does not need the rest."""
    return [cue["finding"] for cue in cues(text)]


def linked(rows):
    """The cues whose statement carried an explicit link to the interpretation."""
    return [cue for cue in rows or () if cue.get("linked")]


def sanitise(rows):
    """Keep only rows shaped the way this module writes them."""
    clean = []
    for row in rows or ():
        if not isinstance(row, dict):
            continue
        finding = str(row.get("finding") or "").strip()
        if not finding or row.get("polarity") not in {"present", "absent", "trend", "uncertain"}:
            continue
        clean.append({
            "finding": finding[:120],
            "polarity": row["polarity"],
            "linked": bool(row.get("linked")),
            "link_marker": str(row.get("link_marker") or "")[:60],
            "contrast": bool(row.get("contrast")),
            "statement": str(row.get("statement") or "")[:300],
            # Which reader saw it. A faculty member reading a cue should know
            # whether the patterns found it or a model was asked.
            "source": "model" if row.get("source") == "model" else "pattern",
        })
    return clean[:24]
