"""What the resident is told at the door, before they ask anything.

Two authored fields and no others: the complaint, in the words of whoever gives
it, and how it began. That is a handover -- enough to start thinking along a
line, and not enough to spare anyone the work of taking a history.

Three things are deliberately absent, and each has somewhere else it belongs:

* **the observables**, which are on the monitor;
* **how the patient looks**, which is in the photograph;
* **everything else the case holds** -- the medications, the past history, the
  exposures, the risk factors. Those are available on asking, and asking for
  them is the resident's work. Handing over the medication list at the door
  would remove the omission the rubric was told, on 2026-09-23, to score.

Reading these two fields rather than authoring a third string is deliberate:
a brief written separately drifts from the history it summarises, and then two
documents disagree about what the patient said.
"""

# The only history a case hands over unasked. Adding a field here hands it to
# every resident in every encounter, so it is a clinical decision and not a
# formatting one.
HANDED_OVER = ("chief_complaint", "onset")

MAX_FACT = 400


def _case(state):
    if not isinstance(state, dict):
        return {}
    spec = state.get("encounter_spec")
    case = spec.get("clinical_case") if isinstance(spec, dict) else None
    return case if isinstance(case, dict) else {}


def _facts(history, field):
    values = history.get(field)
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple)):
        return []
    return [str(value)[:MAX_FACT].strip() for value in values if str(value).strip()]


def brief(state):
    """The handed-over history of one encounter, field by field."""
    case = _case(state)
    history = case.get("history")
    history = history if isinstance(history, dict) else {}
    source = str(case.get("history_source") or "").strip()
    return {
        "source": source,
        "complaint": " ".join(_facts(history, "chief_complaint")),
        "course": " ".join(_facts(history, "onset")),
        "withheld": sorted(field for field in history if field not in HANDED_OVER),
    }


def handover(state, *, prefix="\n\n"):
    """The handover as one short block, or "" when the case authors none.

    Returned ready to append to the initial presentation, which carries the
    age, the sex and what brought them in. Together those are the four things
    a resident is given before they open their mouth.
    """
    item = brief(state)
    lines = [text for text in (item["complaint"], item["course"]) if text]
    if not lines:
        return ""
    if item["source"] and item["source"].strip().lower() not in {"patient", "the patient"}:
        # Who is telling the story changes how much of it to trust, and the
        # resident cannot see who is standing there.
        lines.append(f"History from: {item['source']}.")
    return prefix + " ".join(lines)
