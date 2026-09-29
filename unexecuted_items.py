"""What an order recognised and did not execute, said as what it is.

Faculty decision 3 of 2026-09-25 ("Medicamentos sin efecto modelado"). One
phrase used to cover four different things -- "Recognized but not executed in
this build" -- and the difference matters to whoever reads the record:

* ``not_modelled``: a medicine the resident indicated that the simulator does
  not model. It is the resident's decision and can be assessed as one; it was
  never administered and had no effect.
* ``prescription``: something prescribed for home. A prescription, not a dose.
* ``conditional``: a plan that depends on a condition, not executed now.
* ``repeat``: a repeat of an order given now, with its interval, count and
  condition, not executed now (DF-16b, 2026-09-28).
* ``advice``: what the patient was told, such as when to come back.
* ``prior_treatment``: what the patient received before the resident's care,
  as reported ("Aspirin 300 mg given by EMS", "Ya recibió adrenalina 0,5 mg
  IM"). History, never the resident's order and never a dose given now
  (TD-36, cycle 9).

Two ``not_modelled`` categories are not medicines, and are said as what they
are (TD-26, 2026-09-28; charter §112, §114):

* ``blood_product``: plasma, platelets, cryoprecipitate or whole blood. The
  order stands in the record as the resident's; its physiologic effect is not
  modelled. Nothing says the engine gave its effect, and nothing says the
  resident did not give it.
* ``massive_transfusion``: the activation of the massive transfusion protocol.
  Activating it gives no product by itself; the units given are the ones
  ordered, and none is invented.
* ``massive_transfusion_stop``: the protocol stood down ("deactivate MTP").
  Recorded as the resident's decision; it takes back no unit already given
  (TD-32, cycle 8).

A ``conditional`` whose order is a discharge is said as what it is:

* ``disposition_plan``: a discharge for later or on a condition ("Discharge home
  in 2 hours", "Observar 4 horas y luego alta", "Alta si sigue asintomática").
  It is recorded as the resident's plan and not carried out now; the patient
  stays in the emergency department (TD-39, cycle 9).

Nothing here marks anything as given, and nothing invents a response.
"""
from __future__ import annotations

LABELS = {
    "not_modelled": "indicated; administration and effect not modelled",
    "prescription": "prescription for home; not a dose given here",
    "conditional": "conditional plan; not executed now",
    "repeat": "repeat instruction; not executed now",
    "advice": "advice to the patient",
    "prior_treatment": "received before your care, as reported; not given here",
}

# The same kind said for what is not a medicine (TD-26).
CATEGORY_LABELS = {
    "blood_product": "blood product ordered; physiologic effect not modelled",
    "massive_transfusion": "massive transfusion protocol activated; the activation gives no blood product by itself",
    "massive_transfusion_stop": "massive transfusion protocol stood down; no unit already given is taken back",
    "disposition_plan": "disposition plan; not carried out now",
}
_CATEGORY_MESSAGES = {
    "blood_product": ("Blood product ordered and recorded as your decision: {items}. Its physiologic effect is not "
                      "modelled in this simulator: the order stands in the record, and the patient's course does "
                      "not include its effect."),
    "massive_transfusion": ("Massive transfusion protocol activation recorded: {items}. Activating it gives no blood "
                            "product by itself; the units given are the ones ordered."),
    "massive_transfusion_stop": ("Massive transfusion protocol stood down and recorded as your decision: {items}. "
                                 "No unit already given is taken back."),
    "disposition_plan": ("Recorded as a disposition plan, not carried out now: {items}. The patient stays in the "
                         "emergency department; a plan is not carried out on its own."),
}
_CATEGORY_HELD = {
    "blood_product": "Also in this order, a blood product whose physiologic effect is not modelled: {items}.",
    "massive_transfusion": "Also in this order, the massive transfusion protocol's activation: {items}.",
    "massive_transfusion_stop": "Also in this order, the massive transfusion protocol stood down: {items}.",
    "disposition_plan": "Also in this order, a disposition plan: {items}.",
}


def _kind_of(detail):
    """The kind a detail is said as: its category when that is not a medicine."""
    if detail.get("kind") in ("not_modelled", "conditional") and detail.get("category") in CATEGORY_LABELS:
        return detail["category"]
    return detail.get("kind")


_MESSAGES = {
    "not_modelled": ("Indicated and recorded as your decision: {items}. Its administration and effect "
                     "are not modelled in this simulator, so nothing was given and nothing changed."),
    "prescription": "Prescription for home recorded: {items}. It is a prescription, not a dose given here.",
    "conditional": "Recorded as a conditional plan, not executed now: {items}.",
    "repeat": "Recorded as a repeat instruction, not executed now: {items}.",
    "advice": "Recorded as advice to the patient: {items}.",
    "prior_treatment": ("Recorded as treatment received before your care, as reported: {items}. It is part of "
                        "the history, not your order: nothing was given now."),
}


# What an order may carry and still have nothing to run now (TD-38, cycle 10).
_ONLY_RECORDED = ("conditional", "repeat", "advice", "prior_treatment")


def plans_only(parsed):
    """True when an order carries nothing to run now: only plans, each said by its kind.

    A conditional order, a repeat, advice to the patient or treatment received
    before the resident's care, written alone. The room says each one as
    recorded; nothing runs, nothing is held and no minute passes. The engine's
    generic "Please specify a question, investigation, treatment, or
    reassessment." used to follow, as if nothing had been read (TD-38). A
    medicine indicated alone stays the engine's recorded decision
    (``family_engine.recorded_only``).
    """
    if not isinstance(parsed, dict) or parsed.get("clarification") or parsed.get("actions"):
        return False
    details = [d for d in parsed.get("future_details") or [] if isinstance(d, dict)]
    return (bool(parsed.get("recognized_future_actions")) and bool(details)
            and all(d.get("kind") in _ONLY_RECORDED for d in details))


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
        grouped.setdefault(_kind_of(detail), []).append(str(detail.get("text") or "").strip())
    lines = []
    for kind in ("prior_treatment", "massive_transfusion", "massive_transfusion_stop", "blood_product", "not_modelled",
                 "prescription", "conditional", "disposition_plan", "repeat", "advice"):
        if grouped.get(kind):
            lines.append({**_MESSAGES, **_CATEGORY_MESSAGES}[kind].format(items="; ".join(grouped[kind])))
    unclassified = grouped.get(None) or []
    return lines, unclassified


# The same items while the order that carries them is held: nothing has been
# recorded or given yet. The single sentence these replace called every item a
# medication, and a discharge's follow-up recovered by DF-10 would have been
# announced as a medicine not administered (2026-09-27).
_HELD = {
    "not_modelled": "Also in this order, indicated with administration and effect not modelled: {items}.",
    "prescription": "Also in this order, a prescription for home: {items}.",
    "conditional": "Also in this order, a conditional plan: {items}.",
    "repeat": "Also in this order, a repeat instruction: {items}.",
    "advice": "Also in this order, advice to the patient: {items}.",
    "prior_treatment": "Also in this order, treatment received before your care: {items}.",
}


def held_messages(parsed):
    """What a held order also carries, by kind, without saying it was recorded or given."""
    grouped = {}
    for detail in details_of(parsed):
        grouped.setdefault(_kind_of(detail), []).append(str(detail.get("text") or "").strip())
    lines = [{**_HELD, **_CATEGORY_HELD}[kind].format(items="; ".join(grouped[kind]))
             for kind in ("prior_treatment", "massive_transfusion", "massive_transfusion_stop", "blood_product", "not_modelled",
                          "prescription", "conditional", "disposition_plan", "repeat", "advice") if grouped.get(kind)]
    if grouped.get(None):
        lines.append("Also recognized but not executable in this build: " + ", ".join(grouped[None]) + ".")
    return lines


def trace_labels(event):
    """Each item with what it is, for the learner's Management Trace."""
    return [(str(detail.get("text") or ""), {**LABELS, **CATEGORY_LABELS}.get(_kind_of(detail)))
            for detail in details_of(event)]


def indicated(event):
    """The medicines an event indicated without their administration being modelled."""
    return [d for d in (event or {}).get("future_details") or []
            if isinstance(d, dict) and d.get("kind") in ("not_modelled", "prescription")]
