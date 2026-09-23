"""What each case actually offers the rubric, and what would be a critical event.

Five fields in a report are not five opportunities to assess. A case declares,
per domain, the opportunity it offers and what the resident needs in order to
take it; this module then **verifies against the case itself** that the
declaration is reachable: a study named here has to be among the case's
investigations, an action has to be one the engine executes, an examination has
to be a region the case authors. A declaration that cannot be reached is a
defect in the declaration, not a domain the resident failed.

Critical events are defined here, before the encounter, with stable
identifiers. A model may propose that a defined event occurred. It may not
invent a new event, a new amount, or a new criterion while assessing.
"""

from clinical_cases import FAMILIES, variant_by_id
from rubric import DOMAIN_IDS, CRITICAL_EVENT_KINDS, RubricError


COVERAGE_VERSION = "1.0"


class CoverageError(ValueError):
    """A declaration that does not match the case it describes."""


# Everything the engine can be asked for, by the name the declarations use.
# Derived from the engine rather than restated, so a renamed action breaks the
# declaration instead of silently losing an opportunity.
def _executable_actions():
    from family_parser import NEW_TREATMENT_ACTIONS
    # infusion_adjustment is not a new treatment, which is why it is absent from
    # that set: the interpreter produces it and active_order_context resolves
    # which running infusion it means. It is still something a resident can order.
    return set(NEW_TREATMENT_ACTIONS) | {"consult", "disposition", "reassessment", "examination",
                                         "diagnostic", "reperfusion_referral", "infusion_adjustment"}


def _case(case_or_id):
    if isinstance(case_or_id, str):
        try:
            return variant_by_id(case_or_id)
        except (KeyError, ValueError):
            raise CoverageError(f"Unknown case {case_or_id!r}.") from None
    return case_or_id


def declared(case_or_id):
    """The declaration for this case, or None when it has none yet."""
    case = _case(case_or_id)
    return CASES.get(case["id"])


def verify(case_or_id):
    """Every way this case's declaration fails to match the case. Empty is good."""
    case = _case(case_or_id)
    entry = CASES.get(case["id"])
    if entry is None:
        return [f"{case['id']}: no rubric coverage is declared."]
    problems = []
    # The ECG is always available and is not one of the case's investigations:
    # the engine adds it, which is why it says "...; ecg" when a study is refused.
    studies = set(case.get("investigations", {})) | {"ecg"}
    regions = set(case.get("examination", {})) | {"General appearance", "Breathing", "Peripheral perfusion"}
    actions = _executable_actions()
    domains = entry.get("domains", {})
    for domain in DOMAIN_IDS:
        item = domains.get(domain)
        if item is None:
            if domain in entry.get("not_assessable", {}):
                continue
            problems.append(f"{case['id']} {domain}: neither an opportunity nor a stated reason for its absence.")
            continue
        if not str(item.get("opportunity", "")).strip():
            problems.append(f"{case['id']} {domain}: the opportunity is empty.")
        if not item.get("expected"):
            problems.append(f"{case['id']} {domain}: no expected behaviour.")
        window = item.get("window_min")
        if (not isinstance(window, tuple) or len(window) != 2
                or not all(isinstance(v, int) for v in window) or window[0] >= window[1]):
            problems.append(f"{case['id']} {domain}: the time window is not a clinically stated interval.")
        needs = item.get("requires", {})
        for missing in sorted(set(needs.get("studies", ())) - studies):
            problems.append(f"{case['id']} {domain}: requires study {missing!r}, which this case does not carry.")
        for missing in sorted(set(needs.get("actions", ())) - actions):
            problems.append(f"{case['id']} {domain}: requires action {missing!r}, which the engine does not execute.")
        for missing in sorted(set(needs.get("examination", ())) - regions):
            problems.append(f"{case['id']} {domain}: requires examining {missing!r}, which this case does not author.")
    for reason in entry.get("not_assessable", {}).values():
        if not str(reason).strip():
            problems.append(f"{case['id']}: a domain is declared not assessable without a reason.")
    # What the patient will answer, by the topics this case actually writes. A
    # declaration cannot promise that asking reveals something the case never
    # authored, for the same reason it cannot promise an absent study.
    topics = set(case.get("history", {}))
    for event in entry.get("critical_events", ()):
        problems.extend(_verify_event(case, event, studies, actions, topics))
    return problems


_EVENT_FIELDS = ("event_id", "kind", "action", "trigger", "information_required",
                 "window_min", "alternatives", "evidence_required", "exclusions", "domains",
                 "information_on_asking")

# Faculty decision of 2026-09-23. It travels with every request, because the
# model read "its information is satisfied by the record" as "the resident must
# have obtained it", and refused an event on the strength of the resident's own
# omission.
ASKING_RULE = (
    "Information the case supplies on asking is available whether or not the learner asked. "
    "The patient, or the collateral source the case names, is present for the whole encounter "
    "and answers. A learner who never asked was not deprived of the information; they omitted "
    "to obtain it. So an unasked history never excuses a critical event, and failing to ask "
    "for it is itself an omission the assessment names."
)


def _verify_event(case, event, studies, actions, topics=()):
    problems = []
    for field in _EVENT_FIELDS:
        if field not in event:
            problems.append(f"{case['id']}: critical event is missing {field!r}.")
    identifier = str(event.get("event_id", ""))
    if not identifier or identifier != identifier.strip().lower().replace(" ", "_"):
        problems.append(f"{case['id']}: {identifier!r} is not a stable lower-case identifier.")
    if event.get("kind") not in CRITICAL_EVENT_KINDS:
        problems.append(f"{case['id']} {identifier}: kind must be one of {CRITICAL_EVENT_KINDS}.")
    window = event.get("window_min")
    if not isinstance(window, tuple) or len(window) != 2 or window[0] >= window[1]:
        problems.append(f"{case['id']} {identifier}: no stated window and opportunity.")
    if not event.get("alternatives"):
        problems.append(f"{case['id']} {identifier}: acceptable alternatives are not stated, "
                        "so a valid different choice could be penalised.")
    if not event.get("exclusions"):
        problems.append(f"{case['id']} {identifier}: no exclusion for an engine limitation.")
    for domain in event.get("domains", ()):
        if domain not in DOMAIN_IDS:
            problems.append(f"{case['id']} {identifier}: unknown domain {domain!r}.")
    if not (event.get("information_required") or event.get("information_on_asking")):
        problems.append(f"{case['id']} {identifier}: states nothing that has to be known to judge it.")
    for entry in event.get("information_on_asking", ()):
        if not isinstance(entry, tuple) or len(entry) != 2:
            problems.append(f"{case['id']} {identifier}: an on-asking entry is not a "
                            "(history topic, what it tells them) pair.")
            continue
        topic, tells = entry
        if topic not in topics:
            problems.append(f"{case['id']} {identifier}: promises the history topic "
                            f"{topic!r}, which this case does not author.")
        if not str(tells).strip():
            problems.append(f"{case['id']} {identifier}: the topic {topic!r} is named "
                            "without saying what asking about it would tell them.")
    return problems


def events(case_or_id):
    """The critical events defined for this case, before the encounter."""
    entry = declared(case_or_id)
    return tuple(entry.get("critical_events", ())) if entry else ()


def event_by_id(case_or_id, event_id):
    return next((e for e in events(case_or_id) if e["event_id"] == event_id), None)


def assessable_domains(case_or_id):
    """The domains this case can be scored on at all."""
    entry = declared(case_or_id)
    if entry is None:
        return ()
    return tuple(d for d in DOMAIN_IDS if d in entry.get("domains", {}))


def matrix():
    """Every bank case, its assessable domains and its defined events."""
    rows = []
    for family, definition in sorted(FAMILIES.items()):
        for case in definition.get("variants", []):
            covered = assessable_domains(case["id"])
            rows.append({
                "case_id": case["id"], "family": family,
                "domains": covered, "complete": len(covered) == len(DOMAIN_IDS),
                "not_assessable": dict((declared(case["id"]) or {}).get("not_assessable", {})),
                "critical_events": tuple(e["event_id"] for e in events(case["id"])),
                "problems": verify(case["id"]),
            })
    return rows


CASES = {}
from case_assessment_bank import CASES as _BANK          # noqa: E402
CASES.update(_BANK)
