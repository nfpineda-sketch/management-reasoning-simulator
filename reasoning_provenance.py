"""Where each recorded piece of reasoning came from.

A reader of the Management Trace has to be able to tell four different things
apart, and until now the record told them apart for only one:

* the resident wrote it in this submission;
* the resident wrote it earlier in this encounter, about an earlier decision;
* the resident typed it into the follow-up form after the order was held;
* the application composed the phrase from their other words.

The fifth state is absence, and absence has no entry here: a slot nobody filled
is simply missing, and the trace says "no explicitado" rather than claiming the
resident failed to recognise something.

This module holds no imports on purpose. It is read by the interpreter inside
``app.py``, by the trace analysis and by the documents, and a leaf keeps those
three from having to reach through a Streamlit module to agree on a word.
"""

STATED = "stated"          # written in this submission
CARRIED = "carried"        # stated earlier in this encounter, kept as context
COMPLETED = "completed"    # typed into the follow-up form
COMPOSED = "composed"      # the application's phrasing, not the resident's

ORDER = (STATED, CARRIED, COMPLETED, COMPOSED)

#: The slots a provenance is kept for.
SLOTS = ("problem_representation", "rationale", "management_priority",
         "expected_effect", "reassessment_target", "preservation_goal")

#: Slots that may be carried from an earlier decision. The interpretation of the
#: problem survives a second order in the same encounter; an expectation and a
#: reassessment plan belong to the decision that produced them and are never
#: carried, because they were about a different action.
CARRYABLE = ("problem_representation", "rationale", "management_priority")

LABELS = {
    STATED: "stated in this entry",
    CARRIED: "stated earlier in this encounter",
    COMPLETED: "completed in the follow-up",
    COMPOSED: "composed by the application from your other words",
}

LABELS_ES = {
    STATED: "enunciado en esta entrada",
    CARRIED: "enunciado antes en este encuentro",
    COMPLETED: "completado en el formulario",
    COMPOSED: "compuesto por la aplicación a partir de sus otras palabras",
}

UNSTATED_LABEL = "not stated"
UNSTATED_LABEL_ES = "no explicitado"


def mark(reasoning, source):
    """Record where each filled slot came from, without overwriting what is known.

    A slot already carrying a provenance keeps it: the first hand that wrote it
    is the one the record names. ``derived_slots`` still decides which slots are
    the application's phrasing, so the two records cannot disagree.
    """
    if not reasoning:
        return reasoning
    composed = set(reasoning.get("derived_slots") or ())
    provenance = dict(reasoning.get("slot_provenance") or {})
    for field in SLOTS:
        if not reasoning.get(field):
            provenance.pop(field, None)
            continue
        if field in composed:
            provenance[field] = COMPOSED
        else:
            provenance.setdefault(field, source)
    if provenance:
        reasoning["slot_provenance"] = provenance
    return reasoning


def of(reasoning, field):
    """The provenance of one slot, or None when the slot is absent."""
    if not reasoning or not reasoning.get(field):
        return None
    return (reasoning.get("slot_provenance") or {}).get(field)


def sanitise(values):
    """Keep only provenances this module defines. Anything else is dropped."""
    if not isinstance(values, dict):
        return {}
    return {str(field): values[field] for field in sorted(values)
            if field in SLOTS and values.get(field) in ORDER}
