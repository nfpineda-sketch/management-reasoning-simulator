"""The clinical encounter's screen: the patient on the left, information and writing on the right.

UX of the clinical encounter (faculty instruction of 2026-10-02). Presentation only:
every view here reads what the encounter already holds -- its events, its state and
its Management Trace -- and writes none of it. Nothing is computed, summarised or
revealed that the room had not already given the resident, and nothing is taken out
of the record: what a view leaves out is still in the events and in the Management
Trace, as it was.

The screen has three layers (instruction, section 1):

* the active view: the patient and the monitor (``resuscitation_room``), the
  simulated time and what is still pending, and the room's answer to the latest
  order beside the writing area;
* what can be consulted: four views of what was obtained -- Evolution, History &
  Exam, Results and Orders -- each entry with the minute it was obtained;
* the internal record: every entry, question, field, execution and message, which
  nothing here writes.

The helpers below decide only *where* an entry is shown, from the kind the pipeline
gave it; ``app.py`` draws them with the room's own renderers.
"""
from __future__ import annotations

#: What belongs to the exchange about an order rather than to the patient's course:
#: what the resident wrote, the completed reasoning fields, and the room's questions,
#: notes and messages about an order. Evolution does not repeat them; they stay in the
#: record, the latest exchange's are said beside the writing area and every order's
#: in Orders. Any other kind -- one this list does not know included -- is shown in
#: Evolution, so that an entry is never dropped from view by being unclassified.
EXCHANGE_KINDS = frozenset({"you", "reasoning_completion", "clarification", "prototype",
                            "reasoning_note", "order_cancelled"})

#: The room's messages about an order: the exchange less the resident's own words.
MESSAGE_KINDS = EXCHANGE_KINDS - {"you", "reasoning_completion"}

#: Results: the reports that came back, the tracings acquired and the studies asked
#: for that could not be done.
RESULT_KINDS = frozenset({"diagnostic_result", "diagnostic", "study_not_performed"})

#: The Management Trace statuses of an order, as opposed to information obtained.
ORDER_STATUSES = frozenset({"executed", "terminal_locked", "not_executed", "clarification_required",
                            "deferred"})

#: What an order's line says when it did not run: the decision record's own words for
#: its status (``DECISION n · … · status``), so that the room and the record agree. An
#: order the engine locked because the patient arrested did not run: the room says "not
#: executed" (the record's "terminal locked" reads, in Spanish, as closed at the end of the
#: encounter, which it was not).
STATUS_WORDS = {"clarification_required": "clarification required", "deferred": "Pending"}

#: The room's prompt for an order held for its reasoning. It is transient: the room removes
#: it once the order is completed or cancelled, and while it stands the held order is said
#: by its own block and form.
GATE_PROMPT = "ORDER HELD — REASONING REQUIRED"

#: The resident's own entries: what they wrote, and a completed set of reasoning fields.
ENTRY_KINDS = ("you", "reasoning_completion")


def order_status(entry):
    """``None`` for an order that ran (its line says its actions); else what the record calls it."""
    status = (entry or {}).get("execution_status")
    if status == "executed":
        return None
    return STATUS_WORDS.get(status, "not executed")


def minutes(value):
    """A minute of the encounter, said one way everywhere on the screen: ``14 min``."""
    try:
        return f"{int(value or 0)} min"
    except (TypeError, ValueError):
        return "—"


def _entries(events):
    return [(position, event) for position, event in enumerate(events or []) if isinstance(event, dict)]


def evolution(events):
    """The clinical information the room delivered, newest first, with each entry's position."""
    return [(position, event) for position, event in reversed(_entries(events))
            if event.get("kind") not in EXCHANGE_KINDS]


def history_and_exam(events):
    """What was asked and what was examined, newest first: ``(position, entry, what was asked)``.

    The question, or the region asked for, is the resident's entry written together with
    the answer by the Talk and Examine controls ("Examine: Breathing"). An examination
    that was part of a written order is shown alone: the order is not repeated as its
    question. An examination is never brought up to date: each is shown as it was
    found, at its minute.
    """
    entries = _entries(events)
    rows = []
    for index, (position, event) in enumerate(entries):
        kind = event.get("kind")
        if kind not in ("presentation", "patient_history", "examination"):
            continue
        asked = None
        if kind != "presentation" and index and entries[index - 1][0] == position - 1:
            before = entries[index - 1][1]
            said = str(before.get("text") or "")
            if before.get("kind") == "you" and said and (kind == "patient_history" or said.startswith("Examine: ")):
                asked = said
        rows.append((position, event, asked))
    return list(reversed(rows))


def results(events):
    """Every result received, tracing acquired and study not done, newest first."""
    return [(position, event) for position, event in reversed(_entries(events))
            if event.get("kind") in RESULT_KINDS]


def _ecg_notice(event):
    """The two notices of a 12-lead ECG: the bedside button's and a written order's report."""
    text = str(event.get("text") or "")
    return ((event.get("kind") == "diagnostic" and text.startswith("12-lead ECG acquired"))
            or (event.get("kind") == "diagnostic_result" and text.startswith("ECG: ")))


def _recorded_at(recording):
    """The minute a recording was announced: when it was back, else when it was acquired."""
    for key in ("time_min", "acquired_at_minutes"):
        value = recording.get(key)
        if type(value) in (int, float):
            return value
    return None


def ecg_notices(events, recordings):
    """``{event position: recording position}``: each ECG notice and the one recording it announced.

    Every 12-lead recording is announced once, in the order it was recorded: the ECG
    button announces it as it is acquired, a written order when it is back. The k-th
    notice is therefore the k-th recording. The pairing is used only when that is
    certain -- as many notices as recordings, none announced before its recording
    existed -- and otherwise no notice offers a button. The recordings themselves are
    always listed in Results, where each opens itself.
    """
    notices = [position for position, event in _entries(events) if _ecg_notice(event)]
    recordings = list(recordings or [])
    if not notices or len(notices) != len(recordings):
        return {}
    pairs = {}
    for index, position in enumerate(notices):
        recording = recordings[index]
        at = _recorded_at(recording) if isinstance(recording, dict) else None
        try:
            announced = int(events[position].get("time", 0))
        except (TypeError, ValueError):
            return {}
        if at is None or at > announced:
            return {}
        pairs[position] = index
    return pairs


def viewable(recording):
    """Only an acquired tracing opens; a recording that could not be acquired says why instead."""
    return isinstance(recording, dict) and recording.get("status") == "available"


def _event_count(snapshot):
    value = (snapshot or {}).get("encounter_event_count") if isinstance(snapshot, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def is_message(event):
    """A message of the room about an order, other than the transient prompt of a held one."""
    return (isinstance(event, dict) and event.get("kind") in MESSAGE_KINDS
            and not (event.get("kind") == "clarification" and GATE_PROMPT in str(event.get("text") or "")))


def order_anchor(events, count):
    """The position of the resident's entry an order was recorded for, or ``None``.

    The Management Trace writes ``encounter_event_count`` right after that entry is added.
    The count can run ahead of the events by the room's prompt for a held order, which the
    room removes after the count was taken when the order is completed in free text or by a
    facilitator's override; the entry is therefore the resident's latest one before it.
    """
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        return None
    return max((position for position, event in _entries(list(events or [])[:count])
                if event.get("kind") in ENTRY_KINDS), default=None)


def order_rows(trace, events):
    """Every order and every message of the room about orders, newest first, each once.

    An order of the Management Trace is shown with the room's messages about it: those after
    the resident's entry it was recorded for (``order_anchor``) and before the end of its
    response (the count the room writes once the response is on the record). An order the
    resident wrote that the record holds no entry for -- held, then cancelled; a reply that
    answered nothing -- is shown with its words and the messages that followed it. Any other
    message -- a cancellation, "There are no pending orders to cancel." -- is a row of its own.
    """
    events = list(events or [])
    entries = _entries(events)
    rows, claimed, anchors, recorded = [], set(), set(), []
    for entry in trace or []:
        if not isinstance(entry, dict):
            continue
        anchor = order_anchor(events, _event_count(entry.get("state_before")))
        if anchor is not None:
            anchors.add(anchor)
        if entry.get("execution_status") not in ORDER_STATUSES:
            continue
        recorded.append(str(entry.get("learner_input") or ""))
        end = _event_count(entry.get("state_after"))
        messages = []
        if anchor is not None and end is not None and anchor < end <= len(events):
            messages = [(position, events[position]) for position in range(anchor + 1, end)
                        if is_message(events[position])]
        claimed.update(position for position, _ in messages)
        rows.append({"row": "order", "at": anchor if anchor is not None else -1, "entry": entry,
                     "messages": messages})
    for index, (position, event) in enumerate(entries):
        words = str(event.get("text") or "").strip()
        # An order completed after it was held is recorded with its first words.
        if event.get("kind") != "you" or position in anchors or not words \
                or any(text.startswith(words) for text in recorded):
            continue
        following = []
        for later, other in entries[index + 1:]:
            if other.get("kind") in ENTRY_KINDS:
                break
            if is_message(other) and later not in claimed:
                following.append((later, other))
        if following:                       # a question to the patient has an answer, not a message
            claimed.update(later for later, _ in following)
            rows.append({"row": "unrecorded", "at": position, "event": event, "messages": following})
    rows += [{"row": "message", "at": position, "event": event, "messages": []}
             for position, event in entries if is_message(event) and position not in claimed]
    return sorted(rows, key=lambda row: row["at"], reverse=True)


def latest_exchange(events):
    """The position of the resident's latest entry and the room's messages since then.

    The latest exchange begins at the most recent learner submission
    (``encounter_workspace.encounter_sections``); a completed set of reasoning fields
    begins one too.
    """
    entries = _entries(events)
    start = max((position for position, event in entries if event.get("kind") in ENTRY_KINDS), default=None)
    if start is None:
        return None, []
    return start, [(position, event) for position, event in entries
                   if position > start and event.get("kind") in MESSAGE_KINDS]


def latest_order(trace, events):
    """The Management Trace entry of the latest exchange, when that exchange was an order."""
    start, _ = latest_exchange(events)
    if start is None or not trace:
        return None
    entry = trace[-1]
    if not isinstance(entry, dict) or entry.get("execution_status") not in ORDER_STATUSES:
        return None
    return entry if order_anchor(events, _event_count(entry.get("state_before"))) == start else None


def latest_clarification(events):
    """The room's latest question, which an order still waiting for its answer depends on."""
    return next(((position, event) for position, event in reversed(_entries(events))
                 if event.get("kind") == "clarification"), None)


def pending_studies(state, family_pending):
    """``[(study, minute it is expected or None)]``: what was asked for and is not back.

    The minute is given where the chart already gave it (``pending_investigations``). A
    family engine says when a result is expected only when the resident asks to review it,
    which takes its own minutes; its studies are given without the minute, so that the
    strip tells nothing earlier than the room does (instruction, sections 3 and 13).
    """
    state = state if isinstance(state, dict) else {}
    rows = [(item.get("diagnostic"), None) for item in family_pending or [] if isinstance(item, dict)]
    rows += [(item.get("diagnostic_type"), item.get("available_at_min"))
             for item in state.get("pending_investigations") or [] if isinstance(item, dict)]
    return [(study, at) for study, at in rows if study]


#: The menu that replaces the sidebar during the encounter (instruction, section 11):
#: a small button in the upper left corner, in the band above the room, opening over
#: the screen without moving it. The header band is made transparent and lets clicks
#: through, except on Streamlit's own toolbar, so that the button can be reached.
MENU_CSS = """
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stHeader"],[data-testid="stHeader"] *{pointer-events:none}
[data-testid="stToolbarActions"],[data-testid="stToolbarActions"] *,[data-testid="stAppDeployButton"],
[data-testid="stAppDeployButton"] *,[data-testid="stMainMenu"],[data-testid="stMainMenu"] *,
[data-testid="stStatusWidget"],[data-testid="stStatusWidget"] *{pointer-events:auto}
.st-key-encounter-menu{position:fixed!important;top:.55rem;left:1rem;z-index:999991;width:auto!important}
.st-key-encounter-menu button{min-height:2.1rem;padding:.2rem .8rem;background:#ffffff;border:1px solid #8aa1ae}
"""
