"""Read-only encounter presentation; source text and event order are preserved.

The room's views are drawn by ``encounter_screen`` and ``app.py`` (UX of the clinical
encounter, 2026-10-02). The latest exchange defined here is the one the screen extends to a
completed set of reasoning fields (``encounter_screen.latest_exchange``), and the one the review
that follows the close still shows as "Latest response".
"""


def encounter_sections(events):
    """Group existing events without inventing patient speech or clinical facts.

    The latest exchange begins at the most recent learner submission. Results
    remain in both that exchange and the complete chronological record.
    """
    events = list(events)
    arrival = [event for event in events if event.get("kind") == "presentation"]
    exchanges = [event for event in events if event.get("kind") != "presentation"]
    latest_start = max(
        (index for index, event in enumerate(exchanges) if event.get("kind") == "you"),
        default=0,
    )
    results = [event for event in events if event.get("kind") == "diagnostic_result"]
    return arrival, exchanges[latest_start:], results, events
