"""Which situations a resident has never been in, and which challenge offers them.

Faculty request of 2026-09-23: when the next decision challenge is assigned,
look at what this resident has already met and prefer the one most likely to
present the important things nobody has been able to observe yet.

**Coverage, not scores.** What this reads is which defined critical events the
resident's past cases could have produced -- that is, which safety situations
they have never been placed in. It does not read how they scored, and it must
not: an instrument that chose the next case from its own marks would be
steering the learner by its own output, and the rubric is a pilot that does not
award or withhold anything. "Not yet observed" is a fact about the curriculum;
"scored low" is a judgement about a person.

Nothing here decides the assignment. ``curriculum.assign_challenge`` keeps its
rule -- expose every challenge first, then return to the largest evidence gap
-- and this only orders the candidates it was already choosing between at
random. A resident who has met everything gets the old random pick back.
"""

from clinical_cases import FAMILIES


def events_of(challenge):
    """Every critical event the cases behind one challenge can present."""
    import case_assessment
    events = set()
    for family in challenge.get("families") or ():
        for case in FAMILIES.get(family, {}).get("variants", ()):
            events.update(item["event_id"] for item in case_assessment.events(case["id"]))
    return events


def challenge_events(challenges):
    """The same, for a catalogue, computed once."""
    return {key: events_of(value) for key, value in challenges.items()}


def seen_events(attempts, challenges):
    """Every critical event this resident has already been in a position to meet.

    Read from their completed, non-sandbox encounters: the challenge each one
    was assigned determines which situations the case could have carried,
    whether or not anything was scored afterwards.
    """
    by_challenge = challenge_events(challenges)
    seen = set()
    for attempt in attempts or ():
        if attempt.get("status") != "completed" or attempt.get("is_sandbox"):
            continue
        seen.update(by_challenge.get(attempt.get("challenge_id"), ()))
    return seen


def unmet(attempts, challenges):
    """How many unseen critical events each challenge would newly offer."""
    by_challenge = challenge_events(challenges)
    already = seen_events(attempts, challenges)
    return {key: len(events - already) for key, events in by_challenge.items()}


def explain(attempts, challenges, chosen):
    """One sentence a faculty member can check, for the record."""
    gaps = unmet(attempts, challenges)
    offered = gaps.get(chosen, 0)
    if not offered:
        return ""
    total = len(set().union(*challenge_events(challenges).values())
                if challenges else set())
    remaining = len(set().union(*(challenge_events(challenges).values() or [set()]))
                    - seen_events(attempts, challenges))
    return (f"Offers {offered} safety situation(s) this resident has not been placed in "
            f"before; {remaining} of {total} remain unmet across the catalogue.")
