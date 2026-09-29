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
    if not isinstance(payload, dict):
        return []
    session = payload.get("session")
    if isinstance(session, dict):
        # The frozen copy taken when the encounter closed is the one that matches
        # the trace; the live list is the fallback for a record saved without it.
        events = session.get("encounter_closed_events") or session.get("events") or []
        return events[:MAX_EVENTS] if isinstance(events, list) else []
    # The learner analysis payload carries no session; its frozen event list
    # (the same encounter_closed_events, chosen by analysis_payload_from_session)
    # is the record. Until 2026-09-26 this path returned nothing, so "The
    # history you took" never rendered in production and only a test that
    # injected a session by hand could see it.
    events = payload.get("encounter_events") or []
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
    # A question about pregnancy or the last period is never a question about onset
    # (DF-23 row 8, 2026-09-29), however it is phrased ("when did your last period start?").
    from patient_conversation import asks_about_pregnancy
    not_pregnancy = " \n".join(item["asked"] for item in exchanges
                               if not asks_about_pregnancy(item["asked"])).lower()
    named = set()
    for topic in (topics if topics is not None else TOPIC_PATTERNS):
        text = not_pregnancy if topic == "onset" else asked
        label = HISTORY_TOPIC_LABELS.get(topic, "")
        if label and label.lower() in text:
            named.add(topic)
            continue
        pattern = TOPIC_PATTERNS.get(topic)
        if pattern and re.search(pattern, text, re.I):
            named.add(topic)
    return named


def frozen_topics(record):
    """(topics, source): the history topics this encounter's own case offered.

    L-F01, approved on 2026-09-28: an encounter is read with what belonged to
    it, never with the bank as it stands today. The topics used to come from the
    live bank, so a topic added to a case later showed an old encounter as
    "never asked", a topic removed hid what had been asked, and the critical
    event screening that turns on those questions changed with them.

    They are read from the case frozen with the encounter: the account store's
    encounter column, written once at launch, then the session's own state.
    ``source`` says which reading this is:

    * ``frozen`` -- the encounter carries its case;
    * ``generated`` -- a generated case declared nothing before it was played;
    * ``unavailable`` -- a legacy encounter that carries no case: what its case
      offered then cannot be known, and today's bank is not read in its place.
    """
    record = record if isinstance(record, dict) else {}
    specs = []
    encounter = record.get("encounter")
    if isinstance(encounter, dict):
        specs.append(encounter.get("spec"))
    payload = record.get("payload")
    session = payload.get("session") if isinstance(payload, dict) else None
    if isinstance(session, dict):
        for key in ("encounter_closed_state", "state"):
            state = session.get(key)
            if isinstance(state, dict):
                specs.append(state.get("encounter_spec"))
    for spec in specs:
        case = spec.get("clinical_case") if isinstance(spec, dict) else None
        if not isinstance(case, dict):
            continue
        # A generated case declared no topics. An authored case the model chose
        # from the bank (provenance "ai") is still the authored case, frozen
        # with its history: counted as generated, its encounters lost every
        # "never asked" topic (adversarial review of cycle 6).
        if str(case.get("id") or "").startswith("AI-") or spec.get("case_family") == "generated":
            return (), "generated"
        history = case.get("history")
        if isinstance(history, dict):
            return tuple(history), "frozen"
    # An analysis payload carries the topic names read from the frozen case
    # when it was built, never the case itself (management_trace_store).
    if isinstance(payload, dict) and isinstance(payload.get("history_topics"), list):
        source = payload.get("history_topics_source")
        if source in {"frozen", "generated", "unavailable"}:
            return tuple(str(topic) for topic in payload["history_topics"]), source
    return (), "unavailable"


def review(record, case_id=""):
    """What was asked, what the case offered, and what nobody asked about.

    ``not_named`` is an omission of the learner's, not a limitation of the
    record, and every surface that shows it says so. Only an encounter that
    carries its case can say what it offered; ``topics_source`` says which one
    this is (``frozen_topics``). ``case_id`` is kept for the callers that pass
    it; the topics never come from it.
    """
    exchanges = obtained(record)
    offered, source = frozen_topics(record)
    named = topics_named(exchanges, offered) if offered else topics_named(exchanges)
    return {
        "exchanges": exchanges,
        "asked_anything": bool(exchanges),
        "offered": [{"topic": topic, "label": HISTORY_TOPIC_LABELS.get(topic, topic)}
                    for topic in offered],
        "named": sorted(named),
        "not_named": [{"topic": topic, "label": HISTORY_TOPIC_LABELS.get(topic, topic)}
                      for topic in offered if topic not in named],
        "topics_source": source,
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
    labels = {topic: labels.get(topic) or HISTORY_TOPIC_LABELS.get(topic, topic)
              for topic in set(labels) | set(HISTORY_TOPIC_LABELS)}
    rows = []
    for event in evaluation_basis.resolve(record, case_id or None)["events"] if case_id else ():
        for topic, tells in event.get("information_on_asking", ()):
            if topic in named:
                continue
            rows.append({"event_id": event["event_id"], "topic": topic,
                         "label": labels.get(topic, topic), "tells_them": tells})
    return rows
