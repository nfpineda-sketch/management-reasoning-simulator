"""What an order recognised and did not execute, said as what it is.

Faculty decision 3 of 2026-09-25 ("Medicamentos sin efecto modelado"). One
phrase used to cover four different things -- "Recognized but not executed in
this build" -- and the difference matters to whoever reads the record:

* ``not_modelled``: a medicine the resident indicated that the simulator does
  not model. It is the resident's decision and can be assessed as one; it was
  never administered and had no effect.
* ``prescription``: something prescribed for home. A prescription, not a dose.
* ``conditional``: a plan that depends on a condition, not executed now.
* ``advice``: what the patient was told, such as when to come back.

Nothing here marks anything as given, and nothing invents a response.
"""
from __future__ import annotations

LABELS = {
    "not_modelled": "indicated; administration and effect not modelled",
    "prescription": "prescription for home; not a dose given here",
    "conditional": "conditional plan; not executed now",
    "advice": "advice to the patient",
}

_MESSAGES = {
    "not_modelled": ("Indicated and recorded as your decision: {items}. Its administration and effect "
                     "are not modelled in this simulator, so nothing was given and nothing changed."),
    "prescription": "Prescription for home recorded: {items}. It is a prescription, not a dose given here.",
    "conditional": "Recorded as a conditional plan, not executed now: {items}.",
    "advice": "Recorded as advice to the patient: {items}.",
}


def details_of(parsed_or_event):
    """The classified items, or the bare texts of an older record as unclassified."""
    details = [d for d in (parsed_or_event or {}).get("future_details") or [] if isinstance(d, dict)]
    if details:
        return details
    return [{"text": str(item), "kind": None}
            for item in (parsed_or_event or {}).get("recognized_future_actions") or [] if item]


def messages(parsed):
    """The page's sentences for what was recognised and not executed, by kind."""
    grouped = {}
    for detail in details_of(parsed):
        grouped.setdefault(detail.get("kind"), []).append(str(detail.get("text") or "").strip())
    lines = []
    for kind in ("not_modelled", "prescription", "conditional", "advice"):
        if grouped.get(kind):
            lines.append(_MESSAGES[kind].format(items="; ".join(grouped[kind])))
    unclassified = grouped.get(None) or []
    return lines, unclassified


def trace_labels(event):
    """Each item with what it is, for the learner's Management Trace."""
    return [(str(detail.get("text") or ""), LABELS.get(detail.get("kind")))
            for detail in details_of(event)]


def indicated(event):
    """The medicines an event indicated without their administration being modelled."""
    return [d for d in (event or {}).get("future_details") or []
            if isinstance(d, dict) and d.get("kind") in ("not_modelled", "prescription")]
