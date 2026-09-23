"""The management reasoning rubric: five domains, scored 0-3, and its arithmetic.

A pilot instrument, not a validated one. Its scores are a synthesis grounded in
the published emergency medicine frameworks recorded in
``docs/RUBRICA_MANAGEMENT_REASONING_v1.0.md``; they are not equivalent to ACGME
Milestone levels, Canadian stages, or EPA supervision levels, and they are not
an assessment of a specialist's competence.

Nothing here talks to a provider, a store or a screen. The totals a report
shows are computed by this module from saved values, never by a model: a model
proposes a score per domain and names the events it believes occurred, and the
arithmetic is code's.
"""

from collections.abc import Mapping


VERSION = "1.0-pilot"
# Changing any of the numbers below is a new version. A stored assessment keeps
# the version it was made under, so an update never silently regrades an
# earlier encounter.
LEVELS = (0, 1, 2, 3)
NOT_ASSESSABLE = "not_assessable"
CRITICAL_EVENT_PENALTY = 3
MAX_DOMAIN_SCORE = max(LEVELS)


class RubricError(ValueError):
    """A safe, user-facing failure."""


DOMAINS = {
    "D1": {
        "title": "Recognition of severity and prioritisation",
        "title_es": "Reconocimiento de gravedad y priorización",
        "asks": "Whether the threats were identified, what had to come first was decided, "
                "and the urgency of the action matched the threat.",
        "levels": {
            0: "Misses an observable threat, or delays an essential action in a way that matters clinically.",
            1: "Recognises the problem but orders the priorities wrongly, or needs a substantial corrective prompt.",
            2: "Recognises the threats and prioritises timely actions.",
            3: "Also anticipates plausible deterioration and arranges contingencies without delaying what is essential.",
        },
    },
    "D2": {
        "title": "Clinical assessment and interpretation",
        "title_es": "Evaluación e interpretación clínica",
        "asks": "Whether relevant information was obtained and interpreted, and an explanation "
                "was built that guides decisions.",
        "levels": {
            0: "Omits or misinterprets essential information, compromising management.",
            1: "Assessment incomplete or poorly directed; findings only partly integrated.",
            2: "Obtains and interprets relevant information and considers relevant alternatives.",
            3: "Also integrates uncertainty and discordant data, and selects further information "
               "for its capacity to change management.",
        },
    },
    "D3": {
        "title": "Selection and delivery of safe management",
        "title_es": "Selección y ejecución de un manejo seguro",
        "asks": "Whether the interventions were appropriate, specified enough to be carried out, "
                "and weighed against risk, contraindications and this patient's needs.",
        "levels": {
            0: "Omits an essential intervention, or orders something clearly dangerous in this context.",
            1: "Partly appropriate management, with relevant omissions or insufficient specification.",
            2: "Orders appropriate management, sufficiently specified and safe.",
            3: "Also individualises the management, anticipates adverse effects and coordinates "
               "the complementary measures that belong with it.",
        },
    },
    "D4": {
        "title": "Monitoring and reassessment",
        "title_es": "Seguimiento y reevaluación",
        "asks": "Whether what to watch was defined, delivery and response were checked, "
                "and reassessment happened within an appropriate interval.",
        "levels": {
            0: "Does not check the response or reassess, though there was both need and opportunity.",
            1: "Reassessment late, incomplete, or unrelated to what had to be watched.",
            2: "Checks delivery and response with appropriate variables and intervals.",
            3: "Also sets targets and alarm thresholds, and actively looks for treatment failure or complications.",
        },
    },
    "D5": {
        "title": "Adaptation and continuity of management",
        "title_es": "Adaptación y continuidad del manejo",
        "asks": "Whether the course was integrated, the plan changed or justifiably kept, "
                "support requested, and a safe continuity defined.",
        "levels": {
            0: "Persists with an inadequate plan despite the available evidence, or proposes an unsafe continuity.",
            1: "Recognises the course but adjusts incompletely or late.",
            2: "Updates or justifiably keeps the plan and defines the next safe step.",
            3: "Also sets alternatives for failure, timely escalation, and a handover or follow-up "
               "with its loose ends stated.",
        },
    },
}
DOMAIN_IDS = tuple(DOMAINS)

# D4 is obtaining and checking new information; D5 is using it to decide what
# comes next. Changing the treatment is not required to show adaptation:
# keeping it after checking an adequate response can be right. A 3 is not
# written at greater length, ordered in greater quantity, or treated more
# aggressively; well justified conservative management can earn the maximum.
SEPARATION_NOTE = (
    "Reassessing is obtaining and checking new information. Adapting is using it to decide "
    "what follows. Keeping a treatment after checking an adequate response is an adaptation."
)

CRITICAL_EVENT_KINDS = ("critical_omission", "dangerous_action")


def domain_levels(domain_id):
    try:
        return dict(DOMAINS[domain_id]["levels"])
    except KeyError:
        raise RubricError("Unknown rubric domain.") from None


def valid_score(value):
    """A score is one of the four levels, or the sentinel for no opportunity.

    "Not assessable" is not a zero. A zero is a demonstrated failure where there
    was need, opportunity and means; the sentinel is the absence of one of them.
    """
    return value == NOT_ASSESSABLE or (type(value) is int and value in LEVELS)


def assessable(scores):
    """The domains that carry a number, in rubric order."""
    return tuple(d for d in DOMAIN_IDS if isinstance(scores.get(d), int))


def coverage(scores):
    """How much of the rubric this encounter could be scored against."""
    return {"assessed": len(assessable(scores)), "total": len(DOMAIN_IDS),
            "complete": len(assessable(scores)) == len(DOMAIN_IDS)}


def _confirmed(events):
    """Distinct confirmed critical events. The same event penalises once.

    An event that appears in several turns, or that weighs on more than one
    domain, is still one event. That it can both lower a domain and carry the
    safety penalty is deliberate and is stated wherever the score is shown.
    """
    seen, kept = set(), []
    for event in events or []:
        if not isinstance(event, Mapping) or event.get("status") != "confirmed":
            continue
        identifier = str(event.get("event_id") or "").strip()
        if not identifier or identifier in seen:
            continue
        seen.add(identifier)
        kept.append(event)
    return tuple(kept)


def score(scores, events=()):
    """The whole arithmetic of an assessment, from saved values only.

    A partial assessment keeps its events and their penalties and reports them,
    but has no adjusted total: a subtotal over four domains is not comparable
    with a complete episode and is never normalised into one.
    """
    scores = dict(scores or {})
    for domain, value in scores.items():
        if domain not in DOMAINS or not valid_score(value):
            raise RubricError("A rubric score must be 0-3 or not assessable.")
    seen = assessable(scores)
    confirmed = _confirmed(events)
    penalty = CRITICAL_EVENT_PENALTY * len(confirmed)
    complete = len(seen) == len(DOMAIN_IDS)
    base = sum(scores[d] for d in seen) if complete else None
    return {
        "version": VERSION,
        "coverage": coverage(scores),
        "base": base,
        "maximum": len(DOMAIN_IDS) * MAX_DOMAIN_SCORE if complete else None,
        "penalty": penalty,
        "critical_events": len(confirmed),
        "adjusted": max(0, base - penalty) if complete else None,
        "partial_subtotal": None if complete else sum(scores[d] for d in seen),
        "per_domain": {d: scores.get(d, NOT_ASSESSABLE) for d in DOMAIN_IDS},
    }


def headline(result, language="en"):
    """The one line that always carries the penalty beside the total.

    The safety alert stays visible however high the total is, and a partial
    assessment says so rather than presenting a comparable number.
    """
    events = result["critical_events"]
    if not result["coverage"]["complete"]:
        seen, total = result["coverage"]["assessed"], result["coverage"]["total"]
        if language == "es":
            line = f"Evaluación parcial · {seen} de {total} dominios evaluables"
            return line + (f" · {events} evento(s) crítico(s) confirmado(s), −{result['penalty']}" if events else "")
        line = f"Partial assessment · {seen} of {total} domains assessable"
        return line + (f" · {events} confirmed critical event(s), -{result['penalty']}" if events else "")
    if language == "es":
        line = f"Base {result['base']}/{result['maximum']}"
        if events:
            line += f" · Penalización −{result['penalty']} · Ajustado {result['adjusted']}/{result['maximum']}"
            line += f" · {events} evento(s) crítico(s) confirmado(s)"
        return line
    line = f"Base {result['base']}/{result['maximum']}"
    if events:
        line += f" · Penalty -{result['penalty']} · Adjusted {result['adjusted']}/{result['maximum']}"
        line += f" · {events} confirmed critical event(s)"
    return line


PILOT_NOTICE = (
    "Pilot rubric, version " + VERSION + ". Its scores are not ACGME Milestone levels, "
    "Canadian stages or EPA supervision levels, and inter-rater agreement, the behaviour of "
    "the descriptors and comparability between cases remain to be studied."
)
PILOT_NOTICE_ES = (
    "Rúbrica piloto, versión " + VERSION + ". Sus puntajes no equivalen a niveles de "
    "ACGME, a etapas canadienses ni a niveles de supervisión de APC, y todavía deben "
    "estudiarse el acuerdo entre evaluadores, el funcionamiento de los descriptores y "
    "la comparabilidad entre casos."
)
