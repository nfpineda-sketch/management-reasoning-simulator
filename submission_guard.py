"""A submission is written down before it runs, runs once, and is never lost (Phase 0, 0D).

Pre-pilot measurement safety, 2026-10-06. In a real browser, a zero-gap double click on
*Send* lost the order: nothing executed, nothing was recorded and the text box was cleared
(clinical engine audit §8 G, 3 of 3 trials). There was no submission id anywhere in the
order path, so nothing could tell a repeat from a new order either.

Why it was lost. Streamlit stops a running script, to start the next one, at the first
point where the script touches Streamlit after a click arrives: every drawing call and
every read or write of ``st.session_state`` (Streamlit 1.64, ``SafeSessionState``). The
processing of an order reads and writes the session hundreds of times, so a second click
could stop it anywhere: half applied, never recorded, or saved to the database while the
session kept the revision before it (the next save was then refused as "changed in
another session"). With fast reruns on (Streamlit's default), the second click even ran a
second copy of the page in another thread; ``.streamlit/config.toml`` turns them off.

The guard, with Streamlit's own sequence:

1. The Send button's callback runs at the start of the next run, before anything is
   drawn. ``capture`` writes the raw text with the form's id into the encounter's
   ``submission_log`` (persisted with the encounter), and the page saves it to the
   database at once: the write-ahead.
2. The form's widgets are keyed by that id, and the id changes once it is captured: the
   next form is new and empty. A second click on the old form (a double click, a rapid
   repeat) carries the old id and the same text: it is counted as a duplicate and runs
   nothing.
3. The page processes the oldest ``received`` entry, once. ``begin`` keeps a copy of the
   encounter as it was and marks the entry ``processing``; ``finish`` marks it
   ``processed`` just before the page saves and reruns. While an entry waits, the Send
   button is drawn disabled.
4. An entry still ``processing`` when a run starts belongs to a run that was stopped part
   way. ``recover``, called before anything reads the encounter, puts the encounter back
   as it was before that run began and lets the entry run again, from the start: what
   the stopped run had applied is never kept, and nothing is applied twice. An entry
   stopped twice, or one whose copy is gone, is marked ``interrupted`` and said, never
   run again.

Each of these steps, and the save itself, runs through ``atomic``: on a helper thread
that carries the script's context, where Streamlit does not stop a run, while the script
waits for it. A click arriving meanwhile is handled as soon as the step is complete.

Reloading the page does not re-execute anything: a processed entry stays processed, and
a received one that the reload interrupted is found in the database when the encounter
is resumed and processed once. Two browser sessions on one encounter are kept apart by
the store's revision check, which refuses the later save and says so.
"""
from __future__ import annotations

import contextvars
import threading
import time
import uuid
from copy import deepcopy

LOG_KEY = "submission_log"
NONCE_KEY = "_submission_nonce"
CURRENT_KEY = "_processing_submission"
STATUSES = ("received", "processing", "processed", "interrupted")
TEXT_PREFIX = "learner_text_"
SEND_PREFIX = "learner_send_"
MAX_RETRIES = 1
_SNAPSHOTS: dict[str, dict] = {}
_MAX_SNAPSHOTS = 64
_ATOMIC_THREAD = "submission-guard-atomic"


def atomic(fn, *args, **kwargs):
    """Run ``fn`` so that a click arriving meanwhile cannot stop it part way.

    Streamlit checks for a pending rerun whenever the script's own thread draws or touches
    ``st.session_state``. On another thread that carries the script's context it does not,
    and the session state is shared: ``fn`` runs there while the script waits. Outside a
    Streamlit run (tests, tools), or when already on such a thread, ``fn`` runs directly.
    """
    if threading.current_thread().name == _ATOMIC_THREAD:
        return fn(*args, **kwargs)
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
        ctx = get_script_run_ctx(suppress_warning=True)
    except Exception:  # an installation without the runtime: nothing can stop fn
        ctx = None
    if ctx is None or _in_callback(ctx):
        # A widget callback runs while Streamlit holds the session's lock: a helper thread
        # could not touch the session at all. Callbacks only write the text down.
        return fn(*args, **kwargs)
    box = {}
    context = contextvars.copy_context()

    def run():
        try:
            box["value"] = context.run(fn, *args, **kwargs)
        except BaseException as exc:  # raised again on the script's thread
            box["error"] = exc

    helper = threading.Thread(target=run, name=_ATOMIC_THREAD, daemon=True)
    add_script_run_ctx(helper, ctx)
    helper.start()
    helper.join()
    if "error" in box:
        raise box["error"]
    return box.get("value")


def _in_callback(ctx):
    try:
        from streamlit.runtime.scriptrunner_utils.script_run_context import RunLocation, ThreadState
        if ThreadState.get().run_location == RunLocation.CALLBACK:
            return True
    except Exception:
        pass
    try:  # older Streamlit: the session's lock is held by this thread during callbacks
        return bool(ctx.session_state._lock._is_owned())
    except Exception:
        return False


def new_id():
    return uuid.uuid4().hex[:16]


def nonce(session):
    """The id of the form on the screen; created when there is none."""
    value = session.get(NONCE_KEY)
    if not value:
        value = new_id()
        session[NONCE_KEY] = value
    return value


def text_key(form_id):
    return TEXT_PREFIX + str(form_id)


def send_key(form_id):
    return SEND_PREFIX + str(form_id)


def log(session):
    entries = session.get(LOG_KEY)
    if not isinstance(entries, list):
        entries = []
        session[LOG_KEY] = entries
    return entries


def _entries(session):
    """The log as it is, without creating one."""
    entries = session.get(LOG_KEY) if LOG_KEY in session else None
    return entries if isinstance(entries, list) else []


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def capture(session, form_id, *, entry_point="free_text", minute=None):
    """The Send callback: write the text down before anything runs.

    Returns the entry written, or None when there is nothing to write (an empty box) or
    the click repeats one already written (same form id, same text). The entry reaches the
    database at the top of the run that follows, before anything else (``write_ahead``).
    """
    return atomic(_write_down, session, form_id, entry_point, minute)


def write_ahead(session, save):
    """Save the entries written down and not yet saved, before anything else runs.

    ``save`` writes the encounter to the database and returns the store's refusal, or
    None. Called at the top of the run, in one step with the record of what it saved.
    Returns the entries the database now holds as received.
    """
    def run():
        due = [entry for entry in _entries(session)
               if entry.get("status") == "received" and not entry.get("saved_before_run")]
        if not due or save is None or save() is not None:
            return []
        for entry in due:
            entry["saved_before_run"] = True
        return due
    return atomic(run)


def _write_down(session, form_id, entry_point, minute):
    if minute is None:
        minute = int((session.get("state") or {}).get("sim_time", 0) or 0)
    text = str(session.get(text_key(form_id)) or "").strip()
    if not text:
        return None
    entries = log(session)
    same_form = [entry for entry in entries if entry.get("form_id") == form_id]
    if any(" ".join(entry.get("raw_text", "").split()) == " ".join(text.split()) for entry in same_form):
        # A second click on the same form with the same words: one submission, run once.
        same_form[0]["duplicates"] = int(same_form[0].get("duplicates", 0) or 0) + 1
        return None
    entry = {
        "id": form_id if not same_form else f"{form_id}-{len(same_form) + 1}",
        "form_id": form_id,
        "raw_text": text,
        "entry_point": entry_point,
        "received_at": _now(),
        "received_at_min": minute,
        "status": "received",
        "duplicates": 0,
        "retries": 0,
    }
    entries.append(entry)
    if session.get(NONCE_KEY) == form_id:
        # The next form is a new one: its box is empty and its id is fresh.
        session[NONCE_KEY] = new_id()
    return entry


def pending(session):
    """Entries written and not yet run, oldest first."""
    return [entry for entry in _entries(session) if entry.get("status") == "received"]


def waiting(session):
    """True while a submission waits to run or is running: the Send button is disabled."""
    return any(entry.get("status") in ("received", "processing") for entry in _entries(session))


def begin(session, entry, *, minute=None, fields=()):
    """Claim the submission: keep the encounter as it is, then mark it processing."""
    atomic(_begin, session, entry, minute, tuple(fields))
    return entry


def _begin(session, entry, minute, fields):
    kept = [key for key in fields if key != LOG_KEY]
    _SNAPSHOTS[entry["id"]] = {
        "values": {key: deepcopy(session[key]) for key in kept if key in session},
        "absent": [key for key in kept if key not in session],
    }
    while len(_SNAPSHOTS) > _MAX_SNAPSHOTS:
        _SNAPSHOTS.pop(next(iter(_SNAPSHOTS)))
    entry["status"] = "processing"
    entry["started_at"] = _now()
    entry["started_at_min"] = minute
    session[CURRENT_KEY] = entry["id"]


def finish(session, status="processed"):
    """Mark the submission this run processed; called just before the page saves and reruns."""
    return atomic(_finish, session, status)


def _finish(session, status):
    current = session.get(CURRENT_KEY) if CURRENT_KEY in session else None
    if not current:
        return None
    session[CURRENT_KEY] = None
    for entry in _entries(session):
        if entry.get("id") == current and entry.get("status") == "processing":
            entry["status"] = status
            entry["finished_at"] = _now()
            _SNAPSHOTS.pop(current, None)
            return entry
    return None


def recover(session, fields=()):
    """Undo what a stopped run applied, before anything reads the encounter.

    An entry still ``processing`` when a run starts belongs to a run that was stopped part
    way (a click or a reload arrived while it ran, or it raised). The encounter is put back
    as it was when that entry began, and the entry waits to run again from the start. An
    entry stopped more than ``MAX_RETRIES`` times, or whose copy is gone, is marked
    ``interrupted``: never run again, and said once (``notices``).
    Returns ``{"retried": [...], "interrupted": [...]}``.
    """
    return atomic(_recover, session, tuple(fields))


def _recover(session, fields):
    found = {"retried": [], "interrupted": []}
    for entry in _entries(session):
        if entry.get("status") != "processing":
            continue
        kept = _SNAPSHOTS.pop(entry.get("id"), None)
        retries = int(entry.get("retries", 0) or 0)
        if kept is not None:
            for key in fields:
                if key == LOG_KEY:
                    continue
                if key in kept["values"]:
                    session[key] = deepcopy(kept["values"][key])
                elif key in kept["absent"] and key in session:
                    del session[key]
        if kept is not None and retries < MAX_RETRIES:
            entry["status"] = "received"
            entry["retries"] = retries + 1
            found["retried"].append(entry)
        else:
            entry["status"] = "interrupted"
            entry["interrupted_found_at"] = _now()
            entry["rolled_back"] = kept is not None
            entry["notice_pending"] = True
            found["interrupted"].append(entry)
    if CURRENT_KEY in session and session.get(CURRENT_KEY):
        session[CURRENT_KEY] = None
    return found


def notices(session):
    """Interrupted entries not yet said to the resident; each is said once."""
    def take():
        due = [entry for entry in _entries(session) if entry.get("notice_pending")]
        for entry in due:
            entry["notice_pending"] = False
        return due
    return atomic(take)


def interrupted_message(entry):
    applied = ("nothing of it was applied" if entry.get("rolled_back")
               else "part of it may have been applied")
    return (f'Your order "{entry.get("raw_text", "")}" was interrupted while it was being processed, and '
            f"{applied}. Nothing will be repeated automatically: check the patient's state, and send it "
            "again if it is still needed.")
