"""What the record settles about each defined critical event and each domain's window.

Faculty review of 2026-09-24. Three findings from the batch of ten encounters,
and all three are the same failure seen from a different side: the proposal
said something about the record that the record itself could have settled.

* **An event proposed against its own words.** In one encounter the model
  proposed ``opioid_no_ventilatory_support`` and wrote, in the field where it
  checks the exclusions, that support and reversal had been executed within the
  window "so the critical omission is not present". The resident had ventilated
  with a bag and mask and given naloxone. Nothing between the proposal and the
  penalty read that sentence, or the two executed orders it describes.
* **An event whose literal trigger was in the record and was never proposed.**
  A thrombolysed embolism was never anticoagulated. The model wrote "there is
  no recorded anticoagulation" and turned it into a domain score, because the
  schema only had room for the events it chose to propose.
* **"Not assessable" was never used.** Fifty more domain scores, and none of
  them said that a domain's window had never opened.

This module does not judge any of it. It reads the frozen trace and states, for
every event the case defines, which of its conditions the record settles --
an order executed inside the window, a discharge that happened, a study that
was never asked for -- and, for every domain, whether its declared window had
opened when the encounter closed. The statements travel to the model as facts,
and they are shown to the faculty beside the proposal. A contradiction is never
resolved here: it is named, and the faculty decides.

Deliberately conservative. A status of ``contradicted`` needs an executed order
or a missing one, never a reading of the resident's words; everything that
turns on what the resident *stated* (a contraindication, an observation plan, a
reason for going straight to reperfusion) is left as ``reading`` with the facts
beside it, because a pattern that decides what a sentence means is exactly the
kind of certainty this module exists to withhold.
"""
from __future__ import annotations

import re


# The order a status is read in, strongest first.
STATUSES = ("contradicted", "excluded", "met", "reading", "unscreened")

_EXECUTED = "executed"
_NOT_EXECUTED = ("clarification_required", "not_executed", "deferred")
# Engine narratives and results are not the resident's actions.
_NOT_AN_ORDER = frozenset(("procedure", "diagnostic", "prototype", "clinical_update"))

_NAMES = {
    "bag_mask": ("bag-mask ventilation", "ventilación con bolsa-mascarilla"),
    "naloxone": ("naloxone", "naloxona"),
    "naloxone_infusion": ("a naloxone infusion", "una infusión de naloxona"),
    "oxygen": ("oxygen", "oxígeno"),
    "niv": ("non-invasive ventilation", "ventilación no invasiva"),
    "intubation": ("intubation", "intubación"),
    "anticoagulation": ("anticoagulation", "anticoagulación"),
    "thrombolysis": ("thrombolysis", "trombólisis"),
    "aspirin": ("aspirin", "aspirina"),
    "p2y12": ("a P2Y12 inhibitor", "un inhibidor P2Y12"),
    "bronchodilator": ("a bronchodilator", "un broncodilatador"),
    "continuous_bronchodilator": ("a continuous bronchodilator", "un broncodilatador continuo"),
    "blood": ("blood", "sangre"),
    "fluid": ("crystalloid", "cristaloide"),
    "dextrose": ("dextrose", "glucosa"),
    "dextrose_infusion": ("a dextrose infusion", "una infusión de glucosa"),
    "glucagon": ("glucagon", "glucagón"),
    "oral_carbohydrate": ("oral carbohydrate", "carbohidrato oral"),
    "thiamine": ("thiamine", "tiamina"),
    "antibiotics": ("an antibiotic", "un antibiótico"),
    "epinephrine": ("adrenaline", "adrenalina"),
    "epinephrine_bolus": ("an adrenaline bolus", "un bolo de adrenalina"),
    "epinephrine_im": ("intramuscular adrenaline", "adrenalina intramuscular"),
    "steroid": ("a corticosteroid", "un corticoide"),
    "calcium": ("calcium", "calcio"),
    "atropine": ("atropine", "atropina"),
    "transcutaneous_pacing": ("transcutaneous pacing", "marcapaso transcutáneo"),
    "hemorrhage_control": ("haemorrhage control", "control de la hemorragia"),
    "chest_decompression": ("chest decompression", "descompresión torácica"),
    "stress_test": ("a stress test", "una prueba de esfuerzo"),
    "consult": ("a consultation", "una interconsulta"),
    "disposition": ("a disposition", "un destino"),
    "examination": ("an examination", "un examen"),
    "diagnostic": ("a study", "un estudio"),
    "reassessment": ("a reassessment", "una reevaluación"),
    "dobutamine": ("dobutamine", "dobutamina"),
    "norepinephrine": ("norepinephrine", "norepinefrina"),
}
_STUDIES = {
    "poc_glucose": ("a bedside glucose", "una glicemia capilar"),
    "head_ct": ("a head CT", "una tomografía de cerebro"),
    "urinalysis": ("a urinalysis", "un examen de orina"),
    "temperature": ("a temperature", "una temperatura"),
    "efast": ("an E-FAST", "un E-FAST"),
    "pelvis_xray": ("a pelvis film", "una radiografía de pelvis"),
    "renal_ultrasound": ("a renal ultrasound", "una ecografía renal"),
    "ecg": ("a 12-lead ECG", "un ECG de 12 derivaciones"),
    "abg": ("an arterial gas", "gases arteriales"),
}


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number or number in (float("inf"), float("-inf")) else number


def _say(en, es):
    return {"en": en, "es": es}


def _name(kind, language):
    pair = _NAMES.get(kind, (kind.replace("_", " "), kind.replace("_", " ")))
    return pair[1] if language == "es" else pair[0]


def _minutes(value):
    value = _number(value)
    return "?" if value is None else f"{value:g}"


# --- reading the record -----------------------------------------------------
def _session(record):
    payload = (record or {}).get("payload") or {}
    session = payload.get("session") if isinstance(payload, dict) else None
    return session if isinstance(session, dict) else {}


def _trace(record):
    trace = _session(record).get("management_trace")
    return [event for event in trace if isinstance(event, dict)] if isinstance(trace, list) else []


def facts(record, case_id=""):
    """Everything this module reads, extracted once.

    ``executed`` holds the orders the engine carried out, each with the minute
    it happened and the decision it belongs to. ``withheld`` holds orders the
    resident wrote in a turn that was not executed, which is a different thing
    from never writing them.
    """
    trace = _trace(record)
    executed, withheld, requested, reported, indicated = [], [], [], [], []
    ordinal = 0
    closed = None
    any_executed = False
    for position, event in enumerate(trace):
        status = event.get("execution_status")
        if status in ("executed", "terminal_locked"):
            ordinal += 1
        decision = f"D{ordinal}" if status in ("executed", "terminal_locked") else None
        ref = f"trace:{position}"
        minute = _number(event.get("decision_time_min"))
        response = _number(event.get("response_time_min"))
        if response is not None:
            closed = response if closed is None else max(closed, response)
        interpreted = [a for a in (event.get("interpreted_action") or []) if isinstance(a, dict)]
        if status == _EXECUTED:
            any_executed = True
            for action in interpreted:
                kind = str(action.get("type") or "")
                if kind == "diagnostic" and action.get("diagnostic"):
                    requested.append({"study": str(action["diagnostic"]), "minute": minute,
                                      "ref": ref, "decision": decision})
                if kind in ("reassessment", "examination"):
                    executed.append({"type": kind, "minute": minute, "ref": ref,
                                     "decision": decision, "action": action})
            for action in event.get("action_summaries") or []:
                if not isinstance(action, dict):
                    continue
                kind = str(action.get("type") or "")
                if kind == "diagnostic":
                    study = action.get("diagnostic_type") or action.get("diagnostic")
                    if study:
                        reported.append({"study": str(study), "ref": ref, "decision": decision,
                                         "minute": response if response is not None else minute})
                    continue
                if not kind or kind in _NOT_AN_ORDER or kind in ("reassessment", "examination"):
                    continue
                at = _number(action.get("delivery_starts_at_min"))
                if at is None:
                    at = _number(action.get("time_min"))
                if at is None:
                    at = minute
                executed.append({"type": kind, "minute": at, "ref": ref, "decision": decision,
                                 "action": action})
        elif status in _NOT_EXECUTED:
            for action in interpreted:
                kind = str(action.get("type") or "")
                if kind and kind != "clarification":
                    withheld.append({"type": kind, "minute": minute, "ref": ref,
                                     "status": status, "action": action})
        if status == _EXECUTED:
            # A medicine indicated and not modelled is the resident's decision,
            # never an administration (faculty decision 3, 2026-09-25).
            for item in _indicated_items(event):
                indicated.append({"category": item.get("category") or "other", "text": item.get("text", ""),
                                  "prescription": item.get("kind") == "prescription",
                                  "minute": minute, "ref": ref, "decision": decision})
    narratives = []
    for position, event in enumerate(trace):
        for action in event.get("action_summaries") or []:
            if isinstance(action, dict) and action.get("type") == "procedure":
                narratives.append({"minute": _number(action.get("time_min")),
                                   "text": str(action.get("label") or ""), "ref": f"trace:{position}"})
    asked = set()
    if case_id:
        try:
            import history_review
            asked = set(history_review.review(record, case_id).get("named") or ())
        except Exception:
            asked = set()
    return {"executed": executed, "withheld": withheld, "requested": requested,
            "reported": reported, "narratives": narratives, "closed_at": closed,
            "any_executed": any_executed, "asked_topics": asked, "trace": trace,
            "indicated": indicated}


_ANTICOAGULANT = re.compile(r"\b(?:heparin\w*|enoxaparin\w*|anticoag\w*|hbpm|fondaparinux|rivaroxab\w*|"
                            r"apixab\w*|dabigatran\w*)\b", re.I)
_DEFERRAL = re.compile(r"\b(?:difier\w*|difiero|diferir|posterg\w*|no\s+anticoag\w*|sin\s+anticoag\w*|"
                       r"contraindic\w*|defer\w*|withhold\w*|hold\s+(?:the\s+)?(?:heparin|anticoag)\w*)\b", re.I)
_LATER = re.compile(r"\b(?:despu[eé]s|luego|al\s+terminar|al\s+finalizar|tras|posterior\w*|en\s+\d+\s*(?:h|horas?|min\w*)|"
                    r"after|then|once|following|when)\b", re.I)


def _anticoagulation_statements(trace):
    """Sentences the resident wrote about anticoagulating later, or about deferring it.

    Read from the resident's own words and from what was kept as a plan. A plan
    names an anticoagulant and a later moment; a deferral names one with a reason
    not to give it now. Found statements are shown to the faculty, never decided.
    """
    plans, deferrals = [], []
    for position, event in enumerate(trace or []):
        minute = _number(event.get("decision_time_min"))
        texts = [str(d.get("text") or "") for d in event.get("future_details") or [] if isinstance(d, dict)]
        texts += re.split(r"(?<=[.;])\s+", str(event.get("learner_input") or ""))
        for text in texts:
            text = text.strip()
            if not text or not _ANTICOAGULANT.search(text):
                continue
            row = {"text": text[:200], "minute": minute, "ref": f"trace:{position}"}
            if _DEFERRAL.search(text):
                deferrals.append(row)
            elif _LATER.search(text) or text in texts[:len(event.get("future_details") or [])]:
                plans.append(row)
    return plans, deferrals


def _indicated_items(event):
    """What an event indicated without modelling it, from its kinds or, in an older
    record, from the texts the parser would classify the same way."""
    import unexecuted_items
    items = unexecuted_items.indicated(event)
    if items or event.get("future_details"):
        return items
    from family_parser import _UNMODELED_ORDER, unmodelled_detail
    found = []
    for text in event.get("recognized_future_actions") or []:
        if isinstance(text, str) and _UNMODELED_ORDER.search(text):
            detail = unmodelled_detail(text)
            found.append({"text": text, "kind": "prescription" if detail["prescription"] else "not_modelled",
                          **detail})
    return found


_CATEGORY_NAMES = {
    "antihistamine": ("an antihistamine", "un antihistamínico"),
    "benzodiazepine": ("a benzodiazepine", "una benzodiacepina"),
    "antiemetic": ("an antiemetic", "un antiemético"),
    "h2_blocker": ("an H2 blocker", "un bloqueador H2"),
    "adrenaline_autoinjector": ("an adrenaline auto-injector", "un autoinyector de adrenalina"),
    "other": ("a medicine", "un medicamento"),
}


def _indicated_fact(rows):
    def line(language):
        index = 0 if language == "en" else 1
        parts = []
        for r in rows:
            name = _CATEGORY_NAMES.get(r["category"], _CATEGORY_NAMES["other"])[index]
            when = (f"at {_minutes(r['minute'])} min" if language == "en" else f"a los {_minutes(r['minute'])} min")
            what = ((" as a prescription for home" if language == "en" else " como receta para la casa")
                    if r["prescription"] else "")
            parts.append(f"{name} (\u201c{r['text']}\u201d){what} {when}{_where(r)}")
        return "; ".join(parts)
    return _say("Indicated by the resident, with no administration or effect modelled: " + line("en") + ".",
                "Indicado por el residente, sin administración ni efecto modelados: " + line("es") + ".")


def _within(row, window):
    minute = row.get("minute")
    return minute is not None and window[0] <= minute <= window[1]


def _of(rows, kinds, window=None):
    kinds = set(kinds)
    return [row for row in rows if row["type"] in kinds and (window is None or _within(row, window))]


def _studies(rows, keys, window=None):
    keys = set(keys)
    return [row for row in rows if row["study"] in keys and (window is None or _within(row, window))]


def _where(row):
    decision = row.get("decision")
    return (f" ({decision})" if decision else "")


def _label(row, language):
    """The kind of order, and the agent when the record names one."""
    action = row.get("action") or {}
    if row["type"] == "disposition":
        destination = str(action.get("destination") or "").strip()
        if destination.lower() in ("home", "discharge"):
            return "un alta a domicilio" if language == "es" else "a discharge home"
        if destination:
            return (f"un traslado u hospitalización ({destination})" if language == "es"
                    else f"an admission or transfer ({destination})")
    if row["type"] == "consult" and action.get("service"):
        return (f"una interconsulta ({action['service']})" if language == "es"
                else f"a consultation ({action['service']})")
    agent = str(action.get("agent") or "").strip()
    name = _name(row["type"], language)
    # The agent is said only when the kind is a class ("a bronchodilator
    # (albuterol)"); naloxone given as naloxone is said once.
    same = agent.lower() in (row["type"].lower(), _name(row["type"], "en").lower())
    return f"{name} ({agent})" if agent and not same else name


def _distinct(rows):
    """One line per order: two agents of one kind in one turn are two orders."""
    seen, kept = set(), []
    for row in rows:
        key = (row["type"], row.get("minute"), row.get("ref"),
               str((row.get("action") or {}).get("agent") or ""))
        if key not in seen:
            seen.add(key)
            kept.append(row)
    return kept


def _executed_fact(rows, window):
    # Said as a list after a colon, so no participle has to agree with a noun
    # it cannot see ("ventilación ... ejecutado").
    rows = _distinct(rows)
    en = "; ".join(f"{_label(r, 'en')} at {_minutes(r['minute'])} min{_where(r)}" for r in rows)
    es = "; ".join(f"{_label(r, 'es')} a los {_minutes(r['minute'])} min{_where(r)}" for r in rows)
    return _say(f"Executed inside the window {window[0]}-{window[1]} min: {en}.",
                f"Ejecutado dentro de la ventana {window[0]}-{window[1]} min: {es}.")


def _absent_fact(kinds, window):
    en = ", ".join(_name(k, "en") for k in kinds)
    es = ", ".join(_name(k, "es") for k in kinds)
    return _say(f"None of these was executed between {window[0]} and {window[1]} min: {en}.",
                f"Nada de esto se ejecutó entre los {window[0]} y los {window[1]} min: {es}.")


_WITHHELD = {"clarification_required": ("held for a clarification", "retenido para una aclaración"),
             "not_executed": ("not executed", "no ejecutado"),
             "deferred": ("deferred", "diferido")}


def _withheld_fact(rows):
    rows = _distinct(rows)
    en = "; ".join(f"{_label(r, 'en')} at {_minutes(r['minute'])} min "
                   f"({_WITHHELD.get(r['status'], (r['status'],) * 2)[0]})" for r in rows)
    es = "; ".join(f"{_label(r, 'es')} a los {_minutes(r['minute'])} min "
                   f"({_WITHHELD.get(r['status'], (r['status'],) * 2)[1]})" for r in rows)
    return _say(f"Written but not executed: {en}.", f"Escrito pero no ejecutado: {es}.")


def _closed_fact(closed):
    return _say(f"The encounter closed at {_minutes(closed)} min.",
                f"El encuentro cerró a los {_minutes(closed)} min.")


def _result(status, facts_list, refs=(), reading=None):
    rows = [fact for fact in facts_list if fact]
    if reading:
        rows.append(reading)
    return {"status": status, "facts": rows, "refs": sorted({ref for ref in refs if ref})}


# --- the two shapes most events take ---------------------------------------
def _omission(f, event, absent, *, decisive=True, reading=None, extra_refs=()):
    """A critical omission: something that had to be executed in the window."""
    window = event["window_min"]
    if not f["any_executed"]:
        return _result("excluded", [_say("No order was executed in this encounter.",
                                         "No se ejecutó ninguna orden en este encuentro.")])
    closed = f["closed_at"]
    if closed is not None and closed < window[0]:
        return _result("excluded", [_closed_fact(closed), _say(
            f"The window opens at {window[0]} min and had not opened.",
            f"La ventana abre a los {window[0]} min y no alcanzó a abrirse.")])
    done = _of(f["executed"], absent, window)
    if done:
        return _result("contradicted", [_executed_fact(done, window)], [r["ref"] for r in done])
    rows = [_absent_fact(absent, window)]
    if closed is not None and closed < window[1]:
        rows.append(_say(f"The encounter closed at {_minutes(closed)} min, before the window "
                         f"ended at {window[1]} min.",
                         f"El encuentro cerró a los {_minutes(closed)} min, antes del final de la "
                         f"ventana a los {window[1]} min."))
    withheld = _of(f["withheld"], absent, window)
    if withheld:
        # An order the resident wrote and the application held is not an
        # order never written. Whether they were told what it needed is a
        # reading, and an exclusion of several events turns on it.
        rows.append(_withheld_fact(withheld))
        return _result("reading", rows, [r["ref"] for r in withheld] + list(extra_refs), reading)
    return _result("met" if decisive else "reading", rows, extra_refs, None if decisive else reading)


def _action(f, event, present, *, decisive=True, reading=None, predicate=None):
    """An event that needs something to have been done: a dangerous order, a discharge."""
    window = event["window_min"]
    rows = _of(f["executed"], present, window)
    if predicate is not None:
        rows = [row for row in rows if predicate(row)]
    if not rows:
        en = ", ".join(_name(k, "en") for k in present)
        es = ", ".join(_name(k, "es") for k in present)
        what = ("a discharge" if predicate is _is_discharge else en)
        que = ("un alta" if predicate is _is_discharge else es)
        return _result("contradicted", [_say(
            f"Not executed between {window[0]} and {window[1]} min: {what}.",
            f"No se ejecutó entre los {window[0]} y los {window[1]} min: {que}.")])
    return _result("met" if decisive else "reading", [_executed_fact(rows, window)],
                   [r["ref"] for r in rows], None if decisive else reading)


def _is_discharge(row):
    return str((row.get("action") or {}).get("destination") or "").lower() in ("home", "discharge")


def _observation_before(f, result):
    """What an observation ordered before a discharge had, and had not, completed.

    Ordering hours of observation is not having completed them, and not a safe
    discharge by itself (faculty decision 4, 2026-09-25): the facts say which.
    """
    discharges = [r for r in f["executed"] if r["type"] == "disposition" and _is_discharge(r)
                  and r["minute"] is not None]
    if result["status"] == "contradicted" or not discharges:
        return result
    home = min(r["minute"] for r in discharges)
    observed = [r for r in f["executed"] if r["type"] == "disposition" and r["minute"] is not None
                and r["minute"] <= home
                and str((r.get("action") or {}).get("destination") or "") == "ED observation"]
    if not observed:
        return result
    row = observed[-1]
    hours = (row.get("action") or {}).get("duration_h")
    later = (home - row["minute"]) / 60
    if hours:
        done = later >= float(hours)
        fact = _say(
            f"Emergency department observation for {float(hours):g} h was ordered at {_minutes(row['minute'])} "
            f"min{_where(row)}; the discharge came {later:.1f} h later, so the period was "
            f"{'completed' if done else 'not completed'}.",
            f"Se ordenó observación en urgencias por {float(hours):g} h a los {_minutes(row['minute'])} "
            f"min{_where(row)}; el alta llegó {later:.1f} h después, así que el período "
            f"{'se cumplió' if done else 'no se cumplió'}.")
    else:
        fact = _say(
            f"Emergency department observation was ordered at {_minutes(row['minute'])} min{_where(row)} with "
            f"no duration stated; the discharge came {later:.1f} h later.",
            f"Se ordenó observación en urgencias a los {_minutes(row['minute'])} min{_where(row)} sin "
            f"duración declarada; el alta llegó {later:.1f} h después.")
    result["facts"].append(fact)
    result["refs"] = sorted(set(result["refs"]) | {row["ref"]})
    return result


def _reading(en, es):
    return _say("Needs reading: " + en, "Requiere lectura: " + es)


# --- the events, one by one -------------------------------------------------
def _screen_event(event, f):
    identifier = event["event_id"]
    window = event["window_min"]
    if identifier == "acs_no_antiplatelet":
        return _omission(f, event, ("aspirin", "p2y12"), decisive=False, reading=_reading(
            "whether the ECG was reported and whether a contraindication was stated.",
            "si el ECG estaba informado y si se declaró una contraindicación."))
    if identifier == "acs_provocation_test":
        return _action(f, event, ("stress_test",))
    if identifier == "asthma_no_bronchodilator":
        return _omission(f, event, ("bronchodilator", "continuous_bronchodilator"))
    if identifier == "asthma_no_ventilatory_support":
        return _omission(f, event, ("oxygen", "niv", "bag_mask", "intubation"), decisive=False,
                         reading=_reading("whether the gas or the recorded effort showed ventilatory failure.",
                                          "si los gases o el esfuerzo registrado mostraban falla ventilatoria."))
    if identifier == "gi_no_resuscitation":
        return _omission(f, event, ("blood", "fluid"))
    if identifier == "hypo_no_glucose":
        return _omission(f, event, ("dextrose", "dextrose_infusion", "glucagon", "oral_carbohydrate"))
    if identifier == "hypo_no_thiamine":
        given = _of(f["executed"], ("dextrose", "dextrose_infusion"), window)
        if not given:
            return _result("contradicted", [_say(
                f"No dextrose was executed between {window[0]} and {window[1]} min.",
                f"No se ejecutó glucosa entre los {window[0]} y los {window[1]} min.")])
        thiamine = _of(f["executed"], ("thiamine",), window)
        if thiamine:
            return _result("contradicted", [_executed_fact(thiamine, window)],
                           [r["ref"] for r in thiamine + given])
        return _result("met", [_executed_fact(given, window), _absent_fact(("thiamine",), window)],
                       [r["ref"] for r in given])
    if identifier in ("hypo_unsafe_discharge", "anaphylaxis_unsafe_discharge"):
        return _observation_before(f, _action(
            f, event, ("disposition",), decisive=False, predicate=_is_discharge,
            reading=_reading("whether an observation period, an early review or the return "
                             "criteria were stated with the discharge.",
                             "si con el alta se declaró un período de observación, un control "
                             "precoz o los criterios para volver.")))
    if identifier == "opioid_no_ventilatory_support":
        return _omission(f, event, ("oxygen", "bag_mask", "naloxone", "naloxone_infusion", "intubation"))
    if identifier == "opioid_unsafe_discharge":
        antagonist = _of(f["executed"], ("naloxone", "naloxone_infusion"), window)
        if not antagonist:
            return _result("contradicted", [_say(
                "No antagonist was executed, which the trigger requires before the discharge.",
                "No se ejecutó un antagonista, que el gatillo exige antes del alta.")])
        result = _action(f, event, ("disposition",), decisive=False, predicate=_is_discharge,
                         reading=_reading("whether observation was stated with the discharge.",
                                          "si con el alta se declaró un período de observación."))
        if result["status"] != "contradicted":
            result["facts"].insert(0, _executed_fact(antagonist, window))
            result["refs"] = sorted(set(result["refs"]) | {r["ref"] for r in antagonist})
        return _observation_before(f, result)
    if identifier == "pneumonia_no_antibiotic":
        return _omission(f, event, ("antibiotics",))
    if identifier == "pneumonia_unexamined_altered_state":
        looked = (_studies(f["requested"], ("poc_glucose", "head_ct"), window)
                  + [r for r in _of(f["executed"], ("examination",), window)
                     if re.search(r"neuro|mental|conscious|pupil",
                                  str((r.get("action") or {}).get("region") or ""), re.I)])
        if looked:
            en = "; ".join((_STUDIES.get(r.get("study"), ("a neurological examination",))[0]
                            if r.get("study") else "a neurological examination")
                           + f" at {_minutes(r['minute'])} min{_where(r)}" for r in looked)
            es = "; ".join((_STUDIES.get(r.get("study"), (None, "un examen neurológico"))[1]
                            if r.get("study") else "un examen neurológico")
                           + f" a los {_minutes(r['minute'])} min{_where(r)}" for r in looked)
            return _result("contradicted", [_say(f"Obtained inside the window: {en}.",
                                                 f"Obtenido dentro de la ventana: {es}.")],
                           [r["ref"] for r in looked])
        return _result("met", [_say(
            f"No bedside glucose, neurological examination or head imaging between {window[0]} "
            f"and {window[1]} min.",
            f"Ni glicemia capilar, ni examen neurológico, ni imagen de cerebro entre los "
            f"{window[0]} y los {window[1]} min.")])
    if identifier == "edema_no_ventilatory_support":
        return _omission(f, event, ("oxygen", "niv", "intubation"))
    if identifier == "edema_volume_loading":
        return _action(f, event, ("fluid",), decisive=False, reading=_reading(
            "whether the record showed congestion and no hypovolaemic cause before the bolus.",
            "si el registro mostraba congestión y ninguna causa de hipovolemia antes del bolo."))
    if identifier == "pe_no_anticoagulation":
        result = _omission(f, event, ("anticoagulation",))
        if result["status"] != "met":
            return result
        lysis = _of(f["executed"], ("thrombolysis",), window)
        if not lysis:
            result["facts"].append(_reading(
                "whether a bleeding contraindication was stated.",
                "si se declaró una contraindicación hemorrágica."))
            return result
        # Faculty decision 7 of 2026-09-25. A thrombolysis does not remove the
        # anticoagulation decision. The record tells a documented plan (execution
        # pending), an explicit reason to defer, and a demonstrated omission apart,
        # without a universal minute; the faculty reads what stays ambiguous.
        first = min(row["minute"] for row in lysis if row["minute"] is not None)
        plans, deferrals = _anticoagulation_statements(f["trace"])
        later = [e for e in f["trace"] if e.get("execution_status") == "executed"
                 and _number(e.get("decision_time_min")) is not None and _number(e.get("decision_time_min")) > first]
        facts = [_executed_fact(lysis, window), _absent_fact(("anticoagulation",), window)]
        refs = sorted(set(result["refs"]) | {r["ref"] for r in lysis})
        if plans:
            row = plans[0]
            return _result("reading", facts + [_say(
                f"An anticoagulation plan was documented at {_minutes(row['minute'])} min (\u201c{row['text']}\u201d); "
                "its start was not observed before the encounter closed: a documented plan, execution pending.",
                f"Se documentó un plan de anticoagulación a los {_minutes(row['minute'])} min (\u201c{row['text']}\u201d); "
                "su inicio no se observó antes del cierre: plan documentado, ejecución pendiente.")],
                refs + [row["ref"]], _reading(
                    "whether the plan fits the protocol and the window observed.",
                    "si el plan se ajusta al protocolo y a la ventana observada."))
        if deferrals:
            row = deferrals[0]
            return _result("reading", facts + [_say(
                f"An explicit reason to defer anticoagulation was stated at {_minutes(row['minute'])} min: "
                f"\u201c{row['text']}\u201d.",
                f"Se declaró una razón explícita para diferir la anticoagulación a los {_minutes(row['minute'])} min: "
                f"\u201c{row['text']}\u201d.")], refs + [row["ref"]], _reading(
                    "whether the reason stated justifies deferring it.",
                    "si la razón declarada justifica diferirla."))
        if not later:
            return _result("reading", facts + [_say(
                "The thrombolysis was the last decision before the encounter closed: no later decision "
                "in which an anticoagulation plan could be observed.",
                "La trombólisis fue la última decisión antes del cierre: no hubo una decisión posterior en "
                "la que observar un plan de anticoagulación.")], refs)
        return _result("met", facts + [_say(
            f"No anticoagulation plan and no reason to defer it were stated in the {len(later)} decision(s) "
            "after the thrombolysis: an omission the record demonstrates.",
            f"No se declaró un plan de anticoagulación ni una razón para diferirla en las {len(later)} "
            "decisiones posteriores a la trombólisis: una omisión que el registro demuestra.")], refs)
    if identifier == "pe_unindicated_thrombolysis":
        lysis = _of(f["executed"], ("thrombolysis",), window)
        if not lysis:
            return _action(f, event, ("thrombolysis",))
        first = min(row["minute"] for row in lysis)
        sustained = [n for n in f["narratives"] if n["minute"] is not None and n["minute"] <= first
                     and re.search(r"sustained hypotension", n["text"], re.I)]
        if sustained:
            return _result("excluded", [_executed_fact(lysis, window), _say(
                f"The engine recorded sustained hypotension at {_minutes(sustained[0]['minute'])} min, "
                "before the thrombolytic.",
                f"El motor registró hipotensión sostenida a los {_minutes(sustained[0]['minute'])} min, "
                "antes del trombolítico.")], [r["ref"] for r in lysis])
        return _result("met", [_executed_fact(lysis, window), _say(
            "The engine recorded no sustained hypotension before the thrombolytic.",
            "El motor no registró hipotensión sostenida antes del trombolítico.")],
            [r["ref"] for r in lysis])
    if identifier == "anaphylaxis_no_epinephrine":
        return _omission(f, event, ("epinephrine", "epinephrine_bolus", "epinephrine_im"))
    if identifier == "anaphylaxis_antihistamine_only":
        adjuncts = _of(f["executed"], ("steroid", "bronchodilator", "continuous_bronchodilator"), window)
        # An antihistamine indicated and not modelled is an adjunct the resident
        # chose; it counts as a decision, never as a dose given (decision 3).
        antihistamines = [r for r in f["indicated"] if r["category"] == "antihistamine"
                          and not r["prescription"] and _within(r, window)]
        if not adjuncts and not antihistamines:
            return _action(f, event, ("steroid", "bronchodilator"))
        first = min(row["minute"] for row in adjuncts + antihistamines)
        adrenaline = [r for r in _of(f["executed"], ("epinephrine", "epinephrine_bolus", "epinephrine_im"))
                      if r["minute"] is not None and (r["minute"] <= first or _within(r, window))]
        shown = (([_executed_fact(adjuncts, window)] if adjuncts else [])
                 + ([_indicated_fact(antihistamines)] if antihistamines else []))
        refs = [r["ref"] for r in adjuncts + antihistamines]
        if adrenaline:
            return _result("contradicted", shown + [_say(
                "Adrenaline was executed first, in the same turn or inside the window: " +
                "; ".join(f"{_minutes(r['minute'])} min{_where(r)}" for r in adrenaline) + ".",
                "Se ejecutó adrenalina antes, en el mismo turno o dentro de la ventana: " +
                "; ".join(f"{_minutes(r['minute'])} min{_where(r)}" for r in adrenaline) + ".")],
                refs + [r["ref"] for r in adrenaline])
        if adjuncts:
            return _result("met", shown + [_absent_fact(("epinephrine",), window)], refs)
        # Only an indicated antihistamine: the definition is written for executed
        # steroids and bronchodilators, so this is the faculty's reading.
        return _result("reading", shown + [_absent_fact(("epinephrine",), window), _reading(
            "the definition names an executed steroid or bronchodilator; here the adjunct was an antihistamine "
            "indicated and not modelled, with no adrenaline in the window.",
            "la definición nombra un corticoide o un broncodilatador ejecutado; aquí el coadyuvante fue un "
            "antihistamínico indicado y no modelado, sin adrenalina en la ventana.")], refs)
    if identifier == "anaphylaxis_unexamined_refractory":
        doses = _of(f["executed"], ("epinephrine", "epinephrine_bolus", "epinephrine_im"), window)
        if len(doses) < 2:
            return _result("excluded" if len(doses) == 1 else "contradicted", [_say(
                f"{len(doses)} adrenaline dose(s) executed inside the window; the trigger needs two or more.",
                f"{len(doses)} dosis de adrenalina ejecutada(s) dentro de la ventana; el gatillo exige dos o más.")],
                [r["ref"] for r in doses])
        pursued = _of(f["executed"], ("glucagon", "consult"), window)
        asked = "medications" in f["asked_topics"]
        if pursued or asked:
            rows = [_executed_fact(pursued, window)] if pursued else []
            if asked:
                rows.append(_say("The medication history was asked about.",
                                 "Se preguntó por los medicamentos."))
            return _result("contradicted", rows, [r["ref"] for r in pursued])
        return _result("reading", [_executed_fact(doses, window), _say(
            "No glucagon, no consultation and no medication history inside the window.",
            "Ni glucagón, ni interconsulta, ni pregunta por los medicamentos dentro de la ventana.")],
            [r["ref"] for r in doses], _reading("whether the observables after the doses show an "
                                                "inadequate response.",
                                                "si los observables tras las dosis muestran una "
                                                "respuesta insuficiente."))
    if identifier == "colic_missed_infection":
        discharge = [r for r in _of(f["executed"], ("disposition",), window) if _is_discharge(r)]
        if not discharge:
            return _action(f, event, ("disposition",), predicate=_is_discharge)
        looked = _studies(f["requested"], ("urinalysis", "temperature"))
        if looked:
            return _result("contradicted", [_say(
                "A urinalysis or a temperature was requested before or at the discharge.",
                "Se pidió un examen de orina o una temperatura antes del alta o con ella.")],
                [r["ref"] for r in looked])
        return _result("met", [_executed_fact(discharge, window), _say(
            "Neither a urinalysis nor a temperature was requested anywhere in the record.",
            "No se pidió ni examen de orina ni temperatura en ningún momento del registro.")],
            [r["ref"] for r in discharge])
    if identifier == "pyelo_no_antibiotic":
        return _omission(f, event, ("antibiotics",), decisive=False, reading=_reading(
            "whether the urine and the temperature were in the record.",
            "si el examen de orina y la temperatura estaban en el registro."))
    if identifier == "pyelo_no_source_control":
        urology = [r for r in _of(f["executed"], ("consult",), window)
                   if str((r.get("action") or {}).get("service") or "").lower() == "urology"]
        if urology:
            return _result("contradicted", [_executed_fact(urology, window)], [r["ref"] for r in urology])
        return _result("reading", [_say(
            f"No urology consultation or decompression between {window[0]} and {window[1]} min.",
            f"Ni interconsulta a urología ni descompresión entre los {window[0]} y los {window[1]} min.")],
            (), _reading("whether the renal study reported the dilatation and the urine was infected.",
                         "si el estudio renal informó la dilatación y la orina estaba infectada."))
    if identifier == "pyelo_unsafe_discharge":
        return _action(f, event, ("disposition",), decisive=False, predicate=_is_discharge,
                       reading=_reading("whether the observables at the discharge still carried fever, "
                                        "tachycardia or hypotension.",
                                        "si los observables al alta seguían mostrando fiebre, taquicardia "
                                        "o hipotensión."))
    if identifier == "bradycardia_no_support":
        return _omission(f, event, ("atropine", "transcutaneous_pacing", "epinephrine", "glucagon",
                                    "calcium"), decisive=False,
                         reading=_reading("whether another chronotropic infusion was used.",
                                          "si se usó otra infusión cronotrópica."))
    if identifier == "bradycardia_cause_unexamined":
        support = _of(f["executed"], ("atropine", "transcutaneous_pacing"), window)
        if not support:
            return _result("excluded", [_say("No rate-supporting action was executed.",
                                             "No se ejecutó ninguna acción de soporte de frecuencia.")])
        antidote = _of(f["executed"], ("glucagon", "calcium"), window)
        asked = "medications" in f["asked_topics"]
        if antidote or asked:
            rows = [_executed_fact(antidote, window)] if antidote else []
            if asked:
                rows.append(_say("The medication history was asked about.",
                                 "Se preguntó por los medicamentos."))
            return _result("contradicted", rows, [r["ref"] for r in antidote])
        return _result("reading", [_executed_fact(support, window), _say(
            "No antidote and no medication history inside the window.",
            "Ni antídoto ni pregunta por los medicamentos dentro de la ventana.")],
            [r["ref"] for r in support], _reading("whether the response was inadequate.",
                                                  "si la respuesta fue insuficiente."))
    if identifier == "bradycardia_pacing_unconfirmed":
        pacing = _of(f["executed"], ("transcutaneous_pacing",), window)
        if not pacing:
            return _action(f, event, ("transcutaneous_pacing",))
        first = min(row["minute"] for row in pacing)
        checked = [r for r in _of(f["executed"], ("examination", "reassessment"), window)
                   if r["minute"] is not None and r["minute"] >= first]
        if checked:
            return _result("reading", [_executed_fact(pacing, window), _say(
                "An examination or a reassessment followed the pacing inside the window.",
                "Un examen o una reevaluación siguió al marcapaso dentro de la ventana.")],
                [r["ref"] for r in pacing + checked],
                _reading("whether it named the pulse, the pressure or the perfusion.",
                         "si nombró el pulso, la presión o la perfusión."))
        return _result("met", [_executed_fact(pacing, window), _say(
            "Nothing was examined or reassessed after the pacing inside the window.",
            "No se examinó ni reevaluó nada tras el marcapaso dentro de la ventana.")],
            [r["ref"] for r in pacing])
    if identifier == "hyperk_calcium_awaited_the_laboratory":
        return _omission(f, event, ("calcium",))
    if identifier == "hyperk_no_definitive_removal":
        treated = _of(f["executed"], ("calcium", "dextrose", "bronchodilator"), window)
        if not treated:
            return _result("contradicted", [_say(
                "No calcium or shifting treatment was executed inside the window.",
                "No se ejecutó calcio ni tratamiento de redistribución dentro de la ventana.")])
        removal = _of(f["executed"], ("consult", "disposition"), window)
        if removal:
            return _result("reading", [_executed_fact(removal, window)], [r["ref"] for r in removal],
                           _reading("whether the consultation or the destination addresses dialysis.",
                                    "si la interconsulta o el destino apuntan a la diálisis."))
        return _result("met", [_executed_fact(treated, window), _say(
            "No consultation and no disposition inside the window.",
            "Ni interconsulta ni destino dentro de la ventana.")], [r["ref"] for r in treated])
    if identifier == "trauma_no_hemorrhage_control":
        return _omission(f, event, ("hemorrhage_control",))
    if identifier == "trauma_crystalloid_instead_of_blood":
        fluids = _of(f["executed"], ("fluid",), window)
        volume = sum(_number((r.get("action") or {}).get("volume_ml")) or 0 for r in fluids)
        blood = _of(f["executed"], ("blood",), window)
        if blood:
            return _result("excluded", [_executed_fact(blood, window)], [r["ref"] for r in blood])
        if volume <= 2000:
            return _result("contradicted", [_say(
                f"{volume:g} mL of crystalloid executed inside the window; the trigger needs more than 2000 mL.",
                f"{volume:g} mL de cristaloide ejecutados dentro de la ventana; el gatillo exige más de 2000 mL.")],
                [r["ref"] for r in fluids])
        return _result("met", [_say(
            f"{volume:g} mL of crystalloid and no blood executed between {window[0]} and {window[1]} min.",
            f"{volume:g} mL de cristaloide y nada de sangre entre los {window[0]} y los {window[1]} min.")],
            [r["ref"] for r in fluids])
    if identifier == "trauma_undrained_hemothorax":
        tubes = [r for r in _of(f["executed"], ("chest_decompression",), window)
                 if str((r.get("action") or {}).get("device") or "") != "needle"]
        if tubes:
            return _result("contradicted", [_executed_fact(tubes, window)], [r["ref"] for r in tubes])
        return _omission(f, event, ("chest_decompression",), decisive=False, reading=_reading(
            "whether a needle decompression was followed by a tube inside the window.",
            "si una descompresión con aguja fue seguida por un tubo dentro de la ventana."))
    if identifier == "trauma_drained_and_never_looked_again":
        tubes = [r for r in _of(f["executed"], ("chest_decompression",), window)
                 if str((r.get("action") or {}).get("device") or "") != "needle"]
        if not tubes:
            return _result("contradicted", [_say("No chest tube was executed inside the window.",
                                                 "No se ejecutó un tubo pleural dentro de la ventana.")])
        first = min(row["minute"] for row in tubes)
        after = ([r for r in _studies(f["requested"], ("efast", "pelvis_xray"), window)
                  if r["minute"] is not None and r["minute"] >= first]
                 + [r for r in _of(f["executed"], ("consult",), window)
                    if r["minute"] is not None and r["minute"] >= first
                    and str((r.get("action") or {}).get("service") or "").lower() == "surgery"])
        if after:
            return _result("contradicted", [_say(
                "An E-FAST, a pelvis film or surgery followed the drain inside the window.",
                "Un E-FAST, una radiografía de pelvis o cirugía siguieron al drenaje dentro de la ventana.")],
                [r["ref"] for r in after])
        return _result("reading", [_executed_fact(tubes, window), _say(
            "No E-FAST, pelvis film or surgical consultation after the drain.",
            "Ni E-FAST, ni radiografía de pelvis, ni interconsulta a cirugía tras el drenaje.")],
            [r["ref"] for r in tubes], _reading("whether the observables after the drain still "
                                                "carried instability.",
                                                "si los observables tras el drenaje seguían inestables."))
    return _result("unscreened", [])


def screen_events(record, case_id):
    """One row per event the case defines, in the case's order.

    The events are the ones this encounter is judged against: its frozen copy,
    or for an older record the declarations as they stood until 2026-09-25
    (evaluation_basis). A generated case defines none, and none are invented.
    """
    import evaluation_basis
    defined = evaluation_basis.resolve(record, case_id or None)["events"] if case_id else ()
    if not defined:
        return []
    f = facts(record, case_id)
    rows = []
    for event in defined:
        result = _screen_event(event, f)
        rows.append({"event_id": event["event_id"], "kind": event["kind"],
                     "window_min": list(event["window_min"]), **result})
    return rows


# --- the domains: did the declared window open? ----------------------------
def screen_domains(record, case_id):
    """Whether each domain's declared window had opened when the encounter closed.

    Windows are the case's own, declared before the encounter (``case_assessment``).
    A domain whose window never opened, and for which the resident took none of
    the actions the declaration names, had no real opportunity to be shown:
    that is "not assessable", never a zero. The early closure itself is a fact
    about the encounter and belongs to the domains whose window *was* open.
    """
    import evaluation_basis
    from rubric import DOMAIN_IDS
    entry = evaluation_basis.resolve(record, case_id or None)["declaration"] if case_id else None
    f = facts(record, case_id)
    closed = f["closed_at"]
    rows = []
    for domain in DOMAIN_IDS:
        item = ((entry or {}).get("domains") or {}).get(domain)
        if item is None:
            rows.append({"domain_id": domain, "window_min": None, "window_opened": None,
                         "domain_actions": [], "suggestion": None, "facts": []})
            continue
        window = item["window_min"]
        kinds = tuple((item.get("requires") or {}).get("actions", ()))
        acted = _of(f["executed"], kinds) if kinds else []
        opened = closed is not None and closed >= window[0]
        facts_list = []
        suggestion = None
        if not opened:
            facts_list.append(_say(
                f"The declared window for this domain opens at {window[0]} min; the encounter "
                f"closed at {_minutes(closed)} min.",
                f"La ventana declarada para este dominio abre a los {window[0]} min; el encuentro "
                f"cerró a los {_minutes(closed)} min."))
            if acted:
                facts_list.append(_say(
                    "The resident nonetheless acted in this domain: "
                    + "; ".join(f"{_name(r['type'], 'en')} at {_minutes(r['minute'])} min{_where(r)}"
                                for r in acted) + ".",
                    "El residente igualmente actuó en este dominio: "
                    + "; ".join(f"{_name(r['type'], 'es')} a los {_minutes(r['minute'])} min{_where(r)}"
                                for r in acted) + "."))
            else:
                suggestion = "no_opportunity"
                # Support, never the criterion (faculty decision 8, 2026-09-25):
                # the windows still need reviewing against their cases, and the
                # opportunity also depends on the information, the patient's state
                # and what the simulator could execute.
                facts_list.append(_say(
                    "No action of this domain was taken before the closure. This supports reading it as "
                    "not assessable, not a zero; the window is support, not the criterion: confirm the "
                    "opportunity against the information the learner had, the patient's state and what "
                    "the simulator could execute.",
                    "No hubo acciones de este dominio antes del cierre. Esto apoya leerlo como no evaluable, "
                    "no un cero; la ventana es un apoyo, no el criterio: confirme la oportunidad con la "
                    "información disponible, el estado del paciente y lo que el simulador podía ejecutar."))
        elif closed is not None and closed - window[0] < 5 and not acted:
            # The boundary is stated rather than decided: whether a few
            # minutes inside a window were a real opportunity is the
            # reviewer's reading, and the reviewer needs the minutes.
            facts_list.append(_say(
                f"The window opened at {window[0]} min and the encounter closed "
                f"{_minutes(closed - window[0])} min later, with no action of this domain (a technical "
                "notice, not a boundary between zero and not assessable).",
                f"La ventana abrió a los {window[0]} min y el encuentro cerró "
                f"{_minutes(closed - window[0])} min después, sin acciones de este dominio (un aviso "
                "técnico, no una frontera entre cero y no evaluable)."))
        rows.append({"domain_id": domain, "window_min": list(window), "window_opened": opened,
                     "domain_actions": [{"type": r["type"], "minute": r["minute"], "ref": r["ref"]}
                                        for r in acted],
                     "suggestion": suggestion, "facts": facts_list})
    return rows


def screening(record, case_id):
    """Both readings together, as they travel to the model and to the reviewer."""
    f = facts(record, case_id)
    return {"closed_at_min": f["closed_at"], "events": screen_events(record, case_id),
            "domains": screen_domains(record, case_id),
            # How the encounter ended, as the resident said it ended (decision 9).
            "close": _session(record).get("encounter_close") or None,
            "indicated_not_modelled": [{**row, "facts": [_indicated_fact([row])]} for row in f["indicated"]]}


def for_model(result):
    """The screening in the plain English the proposal request carries."""
    close = result.get("close") or {}
    return {
        "closed_at_min": result["closed_at_min"],
        "close_kind": close.get("kind"),
        "destination_recorded_at_close": close.get("destination_recorded"),
        "events": [{"event_id": row["event_id"], "status": row["status"],
                    "facts": [fact["en"] for fact in row["facts"]], "evidence_refs": row["refs"]}
                   for row in result["events"]],
        "domains": [{"domain_id": row["domain_id"], "window_min": row["window_min"],
                     "window_opened": row["window_opened"],
                     "no_opportunity": row["suggestion"] == "no_opportunity",
                     "facts": [fact["en"] for fact in row["facts"]]}
                    for row in result["domains"]],
        # Decisions with no administration or effect modelled: assessable as
        # decisions, never as doses given (faculty decision 3, 2026-09-25).
        "indicated_not_modelled": [{"evidence_ref": row["ref"], "fact": row["facts"][0]["en"]}
                                   for row in result.get("indicated_not_modelled") or []],
    }


# --- what a proposal says against the record -------------------------------
# The sentence the model wrote in encounter 7, and the shapes it takes. Read
# only as a warning beside a proposal the model already made: it never removes
# an event and never decides one.
_SELF_EXCLUDED = re.compile(
    r"exclusion (?:applies|is met|is satisfied)|(?:omission|event|trigger) (?:is|was) not "
    r"(?:present|met|satisfied)|so the (?:critical )?(?:omission|event) (?:is|was) not|did not occur|"
    r"does not apply|not a critical (?:omission|event)", re.I)


def proposal_flags(proposal_report, result):
    """Where a proposal and the record's own facts disagree, for the reviewer.

    Four kinds, none of which changes the proposal:

    * ``event_contradicted`` -- an event proposed although the record shows
      the order its trigger requires to be absent, or lacks the one it requires;
    * ``event_self_excluded`` -- an event proposed while its own exclusion
      text says the exclusion applies;
    * ``event_not_proposed`` -- every condition the record can settle is met
      and the model did not propose it;
    * ``event_to_read`` -- the record settles part of the trigger (an omission
      verified, a discharge that happened) and the rest turns on what the
      resident stated; the model did not propose it, and its reason is shown;
    * ``domain_without_opportunity`` -- a numeric score on a domain whose
      declared window never opened, with no action of that domain taken.
    """
    from rubric_analysis import event_verdicts, proposed_event_rows
    body = (proposal_report or {}).get("proposal") or {}
    proposed = {row["event_id"]: row for row in proposed_event_rows(proposal_report)}
    verdicts = event_verdicts(proposal_report)
    screens = {row["event_id"]: row for row in result.get("events", [])}
    flags = []
    for event_id, row in proposed.items():
        screen = screens.get(event_id)
        if screen and screen["status"] in ("contradicted", "excluded"):
            flags.append({"kind": "event_contradicted", "event_id": event_id,
                          "status": screen["status"], "facts": screen["facts"],
                          "refs": screen["refs"]})
        if _SELF_EXCLUDED.search(str(row.get("exclusions_checked") or "")):
            flags.append({"kind": "event_self_excluded", "event_id": event_id,
                          "quote": str(row.get("exclusions_checked") or "")})
    for event_id, screen in screens.items():
        if event_id in proposed or screen["status"] not in ("met", "reading"):
            continue
        verdict = verdicts.get(event_id) or {}
        flags.append({"kind": "event_not_proposed" if screen["status"] == "met" else "event_to_read",
                      "event_id": event_id,
                      "facts": screen["facts"], "refs": screen["refs"],
                      "model_verdict": verdict.get("verdict", ""),
                      "model_reason": verdict.get("reason", "")})
    domains = {row["domain_id"]: row for row in result.get("domains", [])}
    for row in body.get("domains", []):
        screen = domains.get(row.get("domain_id"))
        if screen and screen["suggestion"] == "no_opportunity" and isinstance(row.get("score"), int):
            flags.append({"kind": "domain_without_opportunity", "domain_id": row["domain_id"],
                          "score": row["score"], "facts": screen["facts"]})
    return flags


# --- whether a score rests on what the record holds ----------------------------
_ELLIPSIS = re.compile(r"\.{3}|\u2026")
_MAXIMUM = re.compile(r"^\W*(?:maximum\s+level\s+reached|nivel\s+m[aá]ximo\s+alcanzado)\W*$", re.I)
_PLAIN = str.maketrans("áéíóúüñ\u201c\u201d\u2018\u2019", "aeiouun\"\"''")


def _plain(text):
    """Case, accents, quotation marks and spacing folded: how a quote is transcribed."""
    return re.sub(r"\s+", " ", str(text or "").lower().translate(_PLAIN)).strip(" .,;:\"'")


def _said(record):
    """What the resident wrote at each entry of the record, keyed by its evidence ref."""
    said, ordinal = {}, 0
    for position, event in enumerate(_trace(record)):
        status = event.get("execution_status")
        if status in ("executed", "terminal_locked"):
            ordinal += 1
        reasoning = event.get("reasoning") if isinstance(event.get("reasoning"), dict) else {}
        words = [str(event.get("learner_input") or "")] + [
            value for value in reasoning.values() if isinstance(value, str)]
        minutes = {_number(event.get("decision_time_min")), _number(event.get("response_time_min"))}
        said[f"trace:{position}"] = {
            "text": _plain(" ".join(words)), "minutes": {m for m in minutes if m is not None},
            "decision": f"D{ordinal}" if status in ("executed", "terminal_locked") else None,
            "minute": _number(event.get("decision_time_min"))}
    reviews = _session(record).get("precomparison_decision_review")
    for key, answers in (reviews.items() if isinstance(reviews, dict) else ()):
        if isinstance(answers, dict):
            said[f"reflection:{key}"] = {
                "text": _plain(" ".join(v for v in answers.values() if isinstance(v, str))),
                "minutes": None, "decision": None, "minute": None}
    return said


def _quoted(quote, text):
    """Whether the quotation's words are in ``text``, in order; an ellipsis may skip."""
    parts = [_plain(part) for part in _ELLIPSIS.split(str(quote or ""))]
    parts = [part for part in parts if len(part) >= 3]
    at = 0
    for part in parts:
        found = text.find(part, at)
        if found < 0:
            return False
        at = found + len(part)
    return True


def _where_said(entry):
    if entry.get("decision"):
        return (f"decision {entry['decision']} at {_minutes(entry['minute'])} min",
                f"la decisión {entry['decision']}, a los {_minutes(entry['minute'])} min")
    if entry.get("minute") is not None:
        return (f"the entry at {_minutes(entry['minute'])} min",
                f"la entrada de los {_minutes(entry['minute'])} min")
    return ("the reflection cited", "la reflexión citada")


def anchor_flags(proposal_report, record):
    """Where a proposed score is not anchored in the record it cites.

    Evaluator variability, 2026-09-24: the same orders, replayed, give the same
    record -- the encounter is deterministic -- and the model scored it
    differently. One domain named the same omission both times and scored it 3
    and then 2. Nothing here decides which reading is right; it shows the
    reviewer where a score and its own anchor disagree:

    * ``domain_quote_not_in_record`` -- words quoted as the learner's that are
      not in the decision cited (a paraphrase or a translation is not a quote);
    * ``domain_quote_minute_mismatch`` -- a quotation dated at a minute that is
      neither the decision's nor its response's;
    * ``domain_gap_at_maximum`` -- the maximum proposed while naming what the
      record lacks for the level (prompt 1.1);
    * ``domain_gap_missing`` -- a level below the maximum with nothing named as
      missing for the next one, or with "maximum level reached" (prompt 1.1).
    """
    body = (proposal_report or {}).get("proposal") or {}
    said = _said(record)
    flags = []
    for row in body.get("domains", []) if isinstance(body.get("domains"), list) else []:
        if not isinstance(row, dict):
            continue
        domain = row.get("domain_id")
        for item in row.get("learner_evidence") or []:
            if not isinstance(item, dict):
                continue
            entry = said.get(item.get("evidence_ref"))
            if entry is None:
                continue
            where = _where_said(entry)
            quote = str(item.get("quote") or "")
            if not _quoted(quote, entry["text"]):
                flags.append({"kind": "domain_quote_not_in_record", "domain_id": domain,
                              "quote": quote, "refs": [item.get("evidence_ref")],
                              "facts": [_say(f"Quoted from {where[0]}; those words are not in it.",
                                             f"Citado de {where[1]}; esas palabras no están en ella.")]})
            minute = _number(item.get("minute"))
            if entry["minutes"] and minute is not None and minute not in entry["minutes"]:
                flags.append({"kind": "domain_quote_minute_mismatch", "domain_id": domain,
                              "refs": [item.get("evidence_ref")],
                              "facts": [_say(f"Dated {_minutes(minute)} min; it is from {where[0]}.",
                                             f"Fechada a los {_minutes(minute)} min; es de {where[1]}.")]})
        if "next_level_gap" not in row:
            continue
        gap = str(row.get("next_level_gap") or "").strip()
        at_maximum = bool(_MAXIMUM.match(gap))
        score = row.get("score")
        if score == 3 and gap and not at_maximum:
            flags.append({"kind": "domain_gap_at_maximum", "domain_id": domain, "score": score,
                          "quote": gap, "facts": []})
        elif isinstance(score, int) and not isinstance(score, bool) and score < 3 and (not gap or at_maximum):
            flags.append({"kind": "domain_gap_missing", "domain_id": domain, "score": score,
                          "facts": []})
    return flags


FLAG_LABELS = {
    "event_contradicted": ("Proposed, but the record contradicts it",
                           "Propuesto, pero el registro lo contradice"),
    "event_self_excluded": ("Proposed, although its own exclusion check says it does not apply",
                            "Propuesto, aunque su propia revisión de exclusiones dice que no aplica"),
    "event_not_proposed": ("Every condition the record can settle is met, and it was not proposed",
                           "Se cumplen todas las condiciones que el registro puede verificar, y no se propuso"),
    "event_to_read": ("The record settles part of the trigger and it was not proposed: read the rest",
                      "El registro verifica parte del gatillo y no se propuso: lea el resto"),
    "domain_without_opportunity": ("Scored, although its declared window never opened (the window is "
                                   "support: read the opportunity)",
                                   "Puntuado, aunque su ventana declarada nunca se abrió (la ventana es un "
                                   "apoyo: revisar la oportunidad)"),
    "domain_quote_not_in_record": ("The words quoted as the learner's are not in the decision cited",
                                   "Las palabras citadas como del residente no están en la decisión citada"),
    "domain_quote_minute_mismatch": ("A quotation is dated at a minute that is not the decision's",
                                     "Una cita está fechada en un minuto que no es el de la decisión"),
    "domain_gap_at_maximum": ("Scored at the maximum while naming something the record lacks",
                              "Puntuado en el máximo, aunque nombra algo que el registro no muestra"),
    "domain_gap_missing": ("Scored below the maximum without naming what the next level needs",
                           "Puntuado bajo el máximo sin nombrar qué le falta para el nivel siguiente"),
}


def flag_label(kind, language="en"):
    pair = FLAG_LABELS.get(kind, (kind, kind))
    return pair[1] if language == "es" else pair[0]
