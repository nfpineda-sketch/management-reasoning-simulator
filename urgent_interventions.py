"""Urgent interventions run without being held; their reasoning may come afterwards.

Faculty decision 12 of 2026-09-25 ("Procedimientos urgentes: opción B"). An
urgent manoeuvre is executed without waiting for the four categories. What the
resident stated with it, and what they did not, is recorded. The explanation
may be completed later, and then it is recorded as retrospective -- written
after the decision, with the minute it was written -- never as reasoning shown
when the decision was taken. Nothing here reconstructs a working model the
resident never expressed: no earlier interpretation is carried into an urgent
entry and no reader is asked to find one.

The same principle holds for every urgent intervention, not only trauma. An
intervention is urgent here when it is an immediate manoeuvre with nothing to
prepare, where seconds matter: bag-mask ventilation, and the bedside trauma
procedures (chest decompression, haemorrhage control, a pelvic binder). A
procedure prepared over minutes -- an intubation, a synchronised cardioversion
under sedation, transcutaneous pacing -- and an urgent medicine keep the four
categories: an elective cardioversion of a stable atrial fibrillation is not
urgent, and the type of the order cannot tell the two apart. The list is the
faculty's to review (docs/DECISIONES_CLINICAS_PENDIENTES.md).
"""
from __future__ import annotations

URGENT_INTERVENTIONS = frozenset({
    "bag_mask", "chest_decompression", "hemorrhage_control", "pelvic_binder",
})

#: The categories an entry states or leaves unstated, as the record names them.
CATEGORIES = (("working_model", ("problem_representation", "rationale")),
              ("expected_effect", ("expected_effect",)),
              ("reassessment_target", ("reassessment_target",)),
              ("management_priority", ("management_priority",)))

RETROSPECTIVE = "retrospective"
#: The categories a retrospective explanation may fill; a priority is optional anyway.
UNSTATED_CORE = ("working_model", "expected_effect", "reassessment_target")


def is_urgent(parsed):
    """An entry that carries an urgent intervention runs without being held."""
    return any(str(action.get("type")) in URGENT_INTERVENTIONS
               for action in (parsed or {}).get("actions", []) or [] if isinstance(action, dict))


def present_categories(parsed):
    reasoning = (parsed or {}).get("reasoning") or {}
    return [name for name, fields in CATEGORIES if any(reasoning.get(field) for field in fields)]


def awaiting_explanation(trace):
    """The latest urgent entry that left categories unstated and has no retrospective yet."""
    for index in range(len(trace or []) - 1, -1, -1):
        entry = trace[index]
        gate = entry.get("reasoning_gate") or {}
        if (gate.get("status") == "urgent_unheld" and not entry.get("retrospective")
                and any(field in UNSTATED_CORE for field in gate.get("noted") or ())):
            return index
    return None


def record_retrospective(entry, answers, minute):
    """Write a later explanation into an urgent entry, marked as written later.

    Only the categories the entry left unstated are filled, only with what the
    resident typed, and the minute it was written travels with it.
    """
    reasoning = entry.setdefault("reasoning", {})
    provenance = dict(reasoning.get("slot_provenance") or {})
    written = []
    for field, text in (answers or {}).items():
        text = str(text or "").strip()
        if not text or reasoning.get(field):
            continue
        reasoning[field] = text
        provenance[field] = RETROSPECTIVE
        written.append(field)
    reasoning["slot_provenance"] = provenance
    if written:
        entry["retrospective"] = {"written_at_min": minute, "fields": written,
                                  "decision_time_min": entry.get("decision_time_min")}
    return written
