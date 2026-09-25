"""What the resident asked the patient, and what they never asked about.

The history is not in the Management Trace. It is in the encounter's events,
because asking a question is not an order: it costs no simulated time and
changes no observable. That is why, until 2026-09-23, no report and no
assessment could see it, and a model asked to judge a discharge said there was
"no explicit medication history in the encounter" — which was true of what it
had been shown, and false of the encounter.

The rule this module exists to serve (faculty, 2026-09-23): **the patient can
be asked, so the answer was available.** A resident who never asked was not
deprived of the information; they omitted to obtain it. So the reports name
what was never asked about, and the rubric reflects it.

Nothing here judges. It reports what was asked, verbatim, and which of the
topics the case authors were never named in any of it.
"""

import re

from history_topics import HISTORY_TOPIC_LABELS


MAX_EVENTS = 400
MAX_TEXT = 4_000

# One pattern per topic, in both languages, because the question is typed in
# whichever one the resident thinks in. The keys are the case's own history
# keys, so a topic added to a case without a pattern here is reported as
# unmatched rather than silently counted as asked.
TOPIC_PATTERNS = {
    "chief_complaint": r"chief complaint|what brought|why are you here|what happened|"
                       r"qu[eé] (?:le )?(?:pas[oó]|trae)|motivo de consulta|qu[eé] siente",
    "onset": r"onset|when did .*(?:start|begin)|how long|since when|"
             r"cu[aá]ndo (?:empez|comenz|parti)|desde cu[aá]ndo|hace cu[aá]nto|evoluci[oó]n",
    "associated_symptoms": r"associated|other symptom|anything else|review of systems|"
                           r"s[ií]ntomas? asociad|otros s[ií]ntomas|algo m[aá]s",
    "medical_history": r"medical history|past history|previous|comorbid|known (?:illness|condition)|"
                       r"antecedent|historia m[eé]dica|enfermedades? previas?|morbilidad",
    "medications": r"medication|medicines?|drugs? (?:do|does|he|she|they|you)|what .*takes?|"
                   r"prescri|medicament|f[aá]rmac|remedios?|qu[eé] (?:toma|est[aá] tomando)|"
                   r"tratamiento habitual",
    "allergies": r"allerg|alergi",
    "risk_factors": r"risk factor|exposure to|smok|alcohol|drink|travel|immobil|"
                    r"factores? de riesgo|fuma|tabaco|alcohol|viaj|inmovil",
    "chest_pain": r"chest (?:pain|discomfort|pressure)|dolor (?:de )?(?:t[oó]rax|tor[aá]cico|pecho)",
    "breathing": r"breath|dyspn|short of breath|respirat|disnea|respira|falta de aire|ahog",
    "bleeding": r"bleed|blood in|melena|haematem|hematem|sangr|deposiciones negras|vomit[oó] sangre",
    "oral_intake": r"eat|drink|intake|appetite|fasting|com(?:e|ido|iendo)|beb|ingesta|apetito|ayun",
    "exposure": r"expos|contact with|ingest|took (?:a|some|any)|overdose|"
                r"expos|contacto con|consumi|tom[oó] (?:algo|alguna|alg[uú]n)|sobredosis",
    "urinary_symptoms": r"urin|dysuri|voiding|orin|disuria|miccion",
    "neurological_symptoms": r"neurolog|weakness|numb|seizure|confusion|headache|vision|"
                             r"neurol[oó]gic|debilidad|convuls|confusi[oó]n|cefalea|visi[oó]n",
    "leg_symptoms": r"leg|calf|swelling|pierna|pantorrilla|hinchaz[oó]n|edema de",
}


def _events(record):
    payload = (record or {}).get("payload") if isinstance(record, dict) else None
    session = payload.get("session") if isinstance(payload, dict) else None
    if not isinstance(session, dict):
        return []
    # The frozen copy taken when the encounter closed is the one that matches
    # the trace; the live list is the fallback for a record saved without it.
    events = session.get("encounter_closed_events") or session.get("events") or []
    return events[:MAX_EVENTS] if isinstance(events, list) else []


def _text(value):
    return str(value or "")[:MAX_TEXT]


def obtained(record):
    """Every question the resident asked and the answer they were given."""
    exchanges = []
    pending = None
    for event in _events(record):
        if not isinstance(event, dict):
            continue
        kind, text = event.get("kind"), _text(event.get("text"))
        if kind == "you" and text.strip():
            pending = {"minute": int(event.get("time") or 0), "asked": text.strip(),
                       "answered": ""}
        elif kind == "patient_history" and pending is not None:
            exchanges.append({**pending, "answered": text.strip()})
            pending = None
        elif kind == "examination":
            # "Examine: Breathing" is recorded with the same "you" kind as a
            # question. It is an examination, and it belongs to the trace.
            pending = None
    return exchanges


def topics_named(exchanges, topics=None):
    """Which history topics the questions actually reach.

    An explicit topic request ("Ask about medications") is exact. A free-text
    question is matched by the patterns above, which are deliberately broad:
    over-crediting a question the resident did ask is a smaller error than
    telling a faculty member they never asked when they did.
    """
    asked = " \n".join(item["asked"] for item in exchanges).lower()
    if not asked.strip():
        return set()
    named = set()
    for topic in (topics if topics is not None else TOPIC_PATTERNS):
        label = HISTORY_TOPIC_LABELS.get(topic, "")
        if label and label.lower() in asked:
            named.add(topic)
            continue
        pattern = TOPIC_PATTERNS.get(topic)
        if pattern and re.search(pattern, asked, re.I):
            named.add(topic)
    return named


def _case_topics(case_id):
    if not case_id:
        return ()
    try:
        from clinical_cases import variant_by_id
        return tuple(variant_by_id(case_id).get("history", {}))
    except (ImportError, KeyError, ValueError, TypeError):
        return ()


def review(record, case_id=""):
    """What was asked, what the case offered, and what nobody asked about.

    ``not_named`` is an omission of the learner's, not a limitation of the
    record, and every surface that shows it says so.
    """
    exchanges = obtained(record)
    offered = _case_topics(case_id)
    named = topics_named(exchanges, offered) if offered else topics_named(exchanges)
    return {
        "exchanges": exchanges,
        "asked_anything": bool(exchanges),
        "offered": [{"topic": topic, "label": HISTORY_TOPIC_LABELS.get(topic, topic)}
                    for topic in offered],
        "named": sorted(named),
        "not_named": [{"topic": topic, "label": HISTORY_TOPIC_LABELS.get(topic, topic)}
                      for topic in offered if topic not in named],
    }


def unasked_for_events(record, case_id):
    """The topics a defined critical event depends on that nobody asked about.

    Bounded and clinically meaningful: not every topic a case carries matters
    equally, and these are the ones the case declared an event turns on.
    """
    import evaluation_basis
    summary = review(record, case_id)
    named = set(summary["named"])
    labels = {row["topic"]: row["label"] for row in summary["offered"]}
    rows = []
    for event in evaluation_basis.resolve(record, case_id or None)["events"] if case_id else ():
        for topic, tells in event.get("information_on_asking", ()):
            if topic in named:
                continue
            rows.append({"event_id": event["event_id"], "topic": topic,
                         "label": labels.get(topic, topic), "tells_them": tells})
    return rows
