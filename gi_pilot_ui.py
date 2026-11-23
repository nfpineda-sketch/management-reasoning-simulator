"""P3-521 to P3-526: the screens of the controlled DEVELOPMENT pilot of the GI management trace (``gi_pilot``). Streamlit is passed in; nothing here runs unless the
operator named the pilot (``gi_pilot.FLAG``) and the configuration verified.

The participant's side: the pilot notice, ONE pinned case started without an account attempt, a check on every run of the encounter (faculty stop, record, authority,
source control, horizon), the boundary BEFORE an unreviewed definitive control of the bleeding executes, the classified monitor, and the faculty-reviewed management
trace after the encounter. The faculty side: the supervision page (observe, stop, inspect the trace, flag, mark unusable, review the replay). The two never write the
same file of the pilot record, and nothing a faculty member does changes what the participant sees except the stop, which says so.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Mapping

import gi_pilot as gp

LOG = logging.getLogger(__name__)
TITLE = "GI development pilot"
SUPERVISION_TITLE = "GI development pilot · faculty supervision"
UNAVAILABLE = "The development pilot is not available. Tell the supervising faculty member."
ENDED_KEY = "phase3_gi_pilot_closing"


def _on_cloud() -> bool:
    try:
        from account_portal import _on_streamlit_cloud
        return bool(_on_streamlit_cloud())
    except Exception:
        return True            # cannot tell: a hosted deployment is refused, so an unreadable answer is a refusal


def _secret_reader(st: Any) -> Callable:
    """The project's own resolver (``clinical_scene.setting``): secrets, then the environment, with the offline rule that withholds a provider key everywhere. In offline mode an
    AI key therefore resolves to empty here too, which is what makes it unreachable for the whole page; outside offline mode a configured key refuses the pilot."""
    from clinical_scene import setting
    return lambda name: setting(name, "")


#: What the pilot reads of the Phase-3 layer (P3-532): handed over by the page's one crossing on every run (``gate``), never imported here.
_LAYER: gp.Layer | None = None


def layer() -> gp.Layer:
    if _LAYER is None:
        raise gp.PilotRecordError("the page handed the pilot no layer")
    return _LAYER


def gate(st: Any, layer_in: gp.Layer | None, context: Any, accounts: bool) -> dict:
    """Decide the pilot mode for this run and publish it. A pilot that was asked for and cannot be verified stops the page (fails closed). ``layer_in`` is what the page's
    one crossing into the Phase-3 layer hands over (``gi_pilot.layer_from``); this module imports nothing of that layer."""
    global _LAYER
    _LAYER = layer_in
    decision = gp.evaluate(os.environ, accounts=bool(accounts), on_cloud=_on_cloud(), secret=_secret_reader(st), layer=layer_in)
    st.session_state[gp.DECISION_KEY] = decision
    if not decision.get("requested") or decision.get("enabled"):
        return decision
    _close_on_refusal(st, decision)
    st.title(TITLE)
    st.error("DEVELOPMENT PILOT UNAVAILABLE")
    role = ((context or {}).get("user") or {}).get("role")
    if role in gp.FACULTY_ROLES:
        st.write("The development pilot cannot start: its configuration is incomplete or not allowed.")
        for problem in decision.get("problems") or ():
            st.write("• " + str(problem))
    else:
        st.write(UNAVAILABLE)
    st.stop()
    return decision


def _close_on_refusal(st: Any, decision: Mapping) -> None:
    """P3-550 (FD-FINALPILOT-09): the configuration became unavailable (a flag, the grant, the snapshot or the store withdrawn) while this session had a pilot encounter open.
    Nothing of it runs (the page stops here), and the record says so at once: the encounter is ENDED with AUTHORITY_UNAVAILABLE instead of staying ACTIVE, so it can never
    be resumed if the configuration comes back (its next run ends it, ENCOUNTER_CLOSED_IN_RECORD, before any order). A record that cannot be written is left as it is: the
    next run of a restored configuration fails closed on it (PILOT_RECORD_UNAVAILABLE)."""
    info = session(st)
    if info is None or info.get("exit"):
        return
    try:
        store = _store()
        if store.status(info["encounter_id"])["state"] != "ACTIVE":
            return
        try:
            _log_turns(st, store, info)
        except Exception as error:                         # the turns the page already holds are logged when it can; the closing is recorded either way
            LOG.warning("pilot turns not logged at the refusal: %s", error)
        store.append_participant(info["encounter_id"], "ended", {"exit": gp.EXIT_AUTHORITY_UNAVAILABLE, "minute": _minute(st),
                                                                 "reasons": ["the development pilot configuration became unavailable during the encounter"]
                                                                 + [str(problem) for problem in decision.get("problems") or ()][:5]})
    except Exception as error:
        LOG.warning("pilot encounter not closed at the refusal: %s", error)


def enabled(st: Any) -> bool:
    return bool(dict(st.session_state.get(gp.DECISION_KEY) or {}).get("enabled"))


def session(st: Any) -> dict | None:
    """This browser session's pilot encounter, or None."""
    info = st.session_state.get(gp.SESSION_KEY)
    return info if isinstance(info, dict) and gp.ENCOUNTER_ID.match(str(info.get("encounter_id") or "")) else None


def active(st: Any) -> bool:
    return enabled(st) and session(st) is not None


def _store() -> gp.PilotStore:
    root, problem = gp.store_root()
    if root is None:
        raise gp.PilotRecordError(problem)
    return gp.PilotStore(root)


def _configuration() -> dict:
    """What the faculty needs to know about the run; never shown to the participant. The values are the ones the run's configuration names (checked by ``gate``)."""
    from curriculum_runtime import code_version
    return {"grant": gp.NOREPINEPHRINE_GRANT_ID, "pressure_snapshot": gp.PRESSURE_SNAPSHOT_ID, "tone_snapshot": gp.TONE_SNAPSHOT_ID, "environment": gp.DEVELOPMENT_ENVIRONMENT,
            "configuration": {flag: os.environ.get(flag) for flag, _value in layer().configuration}, "code_version": code_version(), "pilot_version": gp.VERSION}


def _arrival(state: dict) -> dict:
    o = dict((state or {}).get("observable") or {})
    sbp, dbp = o.get("sbp"), o.get("dbp")
    try:
        mean = layer().derived_map(sbp, dbp)
    except Exception:
        mean = o.get("map")
    return {"sbp": sbp, "dbp": dbp, "map": mean}


# -- the participant's start ---------------------------------------------------------------------------------------------------------------

def launcher(st: Any, context: Any, initial_state: Any, reset_session: Callable) -> None:
    """The page before an encounter in the pilot deployment: the participant's start, or the faculty supervision page. No other case can be started here."""
    user = dict((context or {}).get("user") or {})
    role = user.get("role")
    if role in gp.FACULTY_ROLES:
        supervision(st, context)
        return
    if role not in gp.PARTICIPANT_ROLES or user.get("id") is None:
        st.error(UNAVAILABLE)
        return
    st.title(TITLE)
    _close_open_encounters(user)
    st.info(gp.PILOT_NOTICE)
    st.write("One synthetic patient with an upper gastrointestinal bleed. Manage the patient as you normally would: write your orders and, when asked, your reasoning. "
             "The encounter covers the first two hours of resuscitation and ends at the development boundary, or earlier if you request definitive control of the bleeding "
             "or end it yourself. Afterwards you see your management trace, for reflection with your supervising faculty member.")
    st.warning("Write each order complete: drug or fluid, dose or volume, duration or rate with its unit, and a reassessment interval. When an order is incomplete, the "
               "simulator holds it and asks what is missing; nothing is carried out and the encounter goes on. When it asks for a rate, write the complete order again "
               "(for example: Increase norepinephrine to 12 mcg/min).")
    st.caption("Supported here: fluids with a stated volume and duration, packed red cells, norepinephrine at an explicit rate in mcg/min (start, change, stop, restart), "
               "reassessment, examination and the case's own tests. A target blood pressure, a relative change or a rate without its unit is held and nothing is given. "
               "Not represented by the development model, and ending the development encounter early if ordered (it is not a judgement of the management): other "
               "medications and other vasopressors, norepinephrine in another unit (mg/min, mcg/kg/min), a nasogastric tube, a urinary catheter and continuous monitoring. "
               "A request for definitive control of the bleeding (gastroenterology, endoscopy, interventional radiology, surgery) ends the encounter at the development boundary.")
    if st.button("Begin the development pilot encounter", type="primary", key="gi_pilot_begin"):
        case_id = gp.PILOT_CASES[0]
        try:
            store = _store()
            participant = gp.participant_ref(user["id"])
            for earlier in store.open_encounters_of(participant):
                store.append_participant(earlier, "interrupted", {"why": "a new pilot encounter was started; an open one is never resumed"})
            from curriculum_runtime import start_pilot_encounter
            start_pilot_encounter(context, initial_state, reset_session, case_id)
            arrival = _arrival(st.session_state.state)
            eid = store.new_encounter(participant=participant, case_id=case_id, arrival=arrival, configuration=_configuration())
        except Exception as error:
            LOG.warning("pilot start refused: %s", error)
            reset_session()
            st.session_state.pop(gp.SESSION_KEY, None)
            st.error("The development pilot encounter could not start. Tell the supervising faculty member.")
            return
        st.session_state[gp.SESSION_KEY] = {"encounter_id": eid, "case_id": case_id, "arrival": arrival, "participant": participant, "logged": 0, "exit": None,
                                            "exit_minute": None, "pending_exit": None}
        st.rerun()


def _close_open_encounters(user: Mapping) -> None:
    """P3-545 (FD-FINALPILOT-09): an encounter is never resumed in a new browser session, so the moment a participant's new session shows the pilot start, any encounter
    of theirs still open in the record is recorded INTERRUPTED (it used to stay ACTIVE until the next start: TD-165 item 13). An open tab of that encounter then ends on its
    next run (ENCOUNTER_CLOSED_IN_RECORD) before it can run another order. A record that cannot be read is left alone here: the start itself fails closed on it."""
    try:
        store = _store()
        participant = gp.participant_ref(user["id"])
        for earlier in store.open_encounters_of(participant):
            store.append_participant(earlier, "interrupted", {"why": "a new session opened the pilot start; an open pilot encounter is never resumed"})
    except Exception as error:
        LOG.warning("pilot: open encounters not closed at the start page: %s", error)


def on_reset(st: Any) -> None:
    """The participant leaves (return to the start, end the attempt, a reset): an open pilot encounter is recorded as LEFT and forgotten by this session."""
    info = session(st)
    if info is None:
        return
    if not info.get("exit"):
        try:
            _store().append_participant(info["encounter_id"], "left", {"minute": _minute(st), "why": "the participant left the encounter before its end"})
        except Exception as error:
            LOG.warning("pilot leave not recorded: %s", error)
    st.session_state.pop(gp.SESSION_KEY, None)
    st.session_state.pop(ENDED_KEY, None)


# -- the participant's encounter -----------------------------------------------------------------------------------------------------------

def _minute(st: Any) -> int:
    try:
        return int(dict(st.session_state.get("state") or {}).get("sim_time", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _plain(value: Any) -> Any:
    """Plain JSON data, refusing anything that is not (never stringified: a stringified mapping would change what the record says)."""
    value = gp.plain(value)
    json.dumps(value)                     # raises on a value that is not JSON: the caller fails closed
    return value


def _log_turns(st: Any, store: gp.PilotStore, info: dict) -> None:
    """Append the page's own management-trace events not yet in the pilot record, and the latest authority artifact (the site the page keeps, read, never opened here)."""
    events = list(st.session_state.get("management_trace") or [])
    observable = dict(dict(st.session_state.get("state") or {}).get("observable") or {})
    for event in events[int(info.get("logged") or 0):]:
        pressure = {"sbp": observable.get("sbp"), "dbp": observable.get("dbp")}
        store.append_participant(info["encounter_id"], "turn", {"minute": _minute(st), "pressure": pressure, "event": _plain(dict(event))})
        info["logged"] = int(info.get("logged") or 0) + 1
    key = layer().site_key
    site = st.session_state.get(key) if key in st.session_state else None
    if site is not None:
        store.write_artifact(info["encounter_id"], _plain(site.artifact()))


def notice(st: Any) -> None:
    if active(st):
        st.caption(gp.PILOT_NOTICE)


def check(st: Any, end: Callable) -> bool:
    """Once per run of an open pilot encounter, before anything can move it: log what happened, then end it on a faculty stop, a record problem, an unavailable or halted
    authority, a definitive-control request (decided by ``barrier``), source control in the engine state, or the development horizon. Returns True when it ended it."""
    info = session(st)
    if info is None or info.get("exit") or not enabled(st):
        return False
    try:
        store = _store()
        _log_turns(st, store, info)
        controls = store.controls(info["encounter_id"])
        recorded = store.status(info["encounter_id"])["state"]
    except Exception as error:
        LOG.warning("pilot record unavailable: %s", error)
        return _end(st, end, gp.EXIT_RECORD_UNAVAILABLE, reasons=[str(error)])
    if recorded == "RECORD_PROBLEM":
        return _end(st, end, gp.EXIT_RECORD_UNAVAILABLE, reasons=["the pilot record does not chain"])
    if recorded != "ACTIVE":
        # P3-531 F2: the record already closed this encounter (another tab of the same participant started a new one, or it was left): it never continues here
        return _end(st, end, gp.EXIT_CLOSED_IN_RECORD, reasons=[f"the pilot record shows it {recorded}"])
    if controls["stop_requested"]:
        return _end(st, end, gp.EXIT_FACULTY_STOP)
    pending = info.get("pending_exit")
    if pending:
        return _end(st, end, pending["exit"], reasons=pending.get("reasons") or [], minute=pending.get("minute"))
    try:
        site = layer().site()          # the page's own helper: the call the page makes on every turn (it orchestrates and decides nothing)
    except Exception:
        site = None
    if site is None:
        return _end(st, end, gp.EXIT_AUTHORITY_UNAVAILABLE)
    if getattr(site, "halted", False):
        return _end(st, end, gp.EXIT_AUTHORITY_STOP, reasons=[str(getattr(site, "halt_reason", "") or "")])
    reasons = gp.engine_source_control(st.session_state.state)
    if reasons:
        return _end(st, end, gp.EXIT_ENGINE_SOURCE_CONTROL, reasons=reasons)
    if _minute(st) >= gp.HORIZON_MIN:
        return _end(st, end, gp.EXIT_HORIZON)
    return False


def _end(st: Any, end: Callable, exit_kind: str, *, reasons: list | None = None, minute: int | None = None) -> bool:
    info = session(st)
    info["exit"], info["exit_minute"] = exit_kind, (_minute(st) if minute is None else minute)
    info["pending_exit"] = None
    try:
        store = _store()
        _log_turns(st, store, info)
        store.append_participant(info["encounter_id"], "ended", {"exit": exit_kind, "minute": info["exit_minute"], "reasons": list(reasons or [])})
    except Exception as error:
        LOG.warning("pilot end not recorded: %s", error)
        info["record_problem"] = str(error)
    end()
    return True


def barrier(st: Any, orders: Any, minute: int, *, actions: Any = None, text: Any = None) -> bool:
    """P3-521 (FD-PILOT-04) and P3-541 (FD-FINALPILOT-05): True when this turn requests definitive control of the bleeding and must NOT run. Called by the page after the turn's
    orders are in the ledger and BEFORE the engine executes anything. It reads, in this order: the actions the engine is about to execute (STRUCTURAL: an executed consultation of
    a definitive service is the only way the earlier engine reaches a haemostasis in this case), the turn's orders, and the turn's own words when the reader made no order. The
    page records the turn as written and not carried out; the next run ends the encounter at the boundary."""
    info = session(st)
    if info is None or info.get("exit") or not enabled(st):
        return False
    structural = gp.definitive_actions(actions)
    found = structural + gp.definitive_intent(orders, None if text is None else str(text))
    if not found:
        return False
    info["pending_exit"] = {"exit": gp.EXIT_DEFINITIVE_REQUEST, "minute": int(minute),
                            "reasons": [str(item.get("canonical") or item.get("span") or item.get("service") or item.get("class") or item.get("type")) for item in found],
                            "structural": bool(structural)}
    return True


def mark_not_carried_out(turn: Any) -> None:
    """The fate of every order of a boundary turn: recorded, not carried out (the ledger's own fate words; nothing acted on the patient)."""
    import order_ledger as L
    for order in (turn or {}).get("orders") or ():
        L.set_fate(order, "RECORDED_NOT_MODELLED", "development pilot boundary: a request for definitive control of the bleeding ends the encounter; nothing in this turn was carried out",
                   minute=None, modelled_effect=False,
                   receipt=f'Recorded, not carried out: "{order.get("span") or order.get("canonical")}". Development pilot boundary.')


# -- what the participant sees: mental status and the monitor ------------------------------------------------------------------------------

def ne_given(st: Any) -> bool:
    return gp.norepinephrine_given(st.session_state.get("order_ledger") or [])


#: P3-542 (FD-FINALPILOT-06): in Talk mode the earlier model decides whether the patient can answer from ITS mental status, so the answer itself would show a mental status the
#: development model does not represent under a vasopressor. Once norepinephrine has been given, questions to the patient are not offered (the history already obtained stays
#: in the chart); nothing in the engine changes.
TALK_WITHHELD = ("Questions to the patient are not available once norepinephrine has been given in this development pilot: the development model does not represent mental "
                 "status on a vasopressor, and whether the patient can answer would show it. The history already obtained stays in the chart.")


def talk_withheld(st: Any) -> bool:
    """True when the pilot does not offer Talk mode (a pilot encounter in which norepinephrine has been given)."""
    try:
        return bool(active(st) and ne_given(st))
    except Exception:
        return True


def cells(st: Any, cells_in: Any, mental_labels: Any) -> Any:
    return gp.display_cells(cells_in, ne_given(st), mental_labels) if active(st) else cells_in


def update_text(st: Any, text: Any) -> Any:
    return gp.display_update_text(text, ne_given(st)) if active(st) else text


def examination_text(st: Any, text: Any) -> Any:
    return gp.display_examination(text, ne_given(st)) if active(st) else text


def appearance(st: Any) -> Callable | None:
    """The room's appearance line transform in the pilot (None outside it)."""
    if not active(st):
        return None
    given = ne_given(st)
    return lambda summary: gp.display_appearance(summary, given)


def withheld_note(st: Any) -> None:
    if active(st) and ne_given(st):
        st.caption(gp.MENTAL_STATUS_WITHHELD_NOTE)


# -- after the encounter: the participant's trace ------------------------------------------------------------------------------------------

def _closing(st: Any) -> dict:
    """The participant's trace, extracted from the PILOT RECORD (the logged turns and the artifact) so that what is shown is what the faculty replay checks. Written once."""
    cached = st.session_state.get(ENDED_KEY)
    info = session(st)
    if isinstance(cached, dict) and cached.get("encounter_id") == info["encounter_id"]:
        return cached
    try:
        store = _store()
        _log_turns(st, store, info)
        if not info.get("exit"):
            info["exit"], info["exit_minute"] = gp.EXIT_PARTICIPANT_FINISHED, _minute(st)
            store.append_participant(info["encounter_id"], "ended", {"exit": info["exit"], "minute": info["exit_minute"], "reasons": []})
        logs = store.logs(info["encounter_id"])
        if logs["problems"]:
            raise gp.PilotRecordError("; ".join(logs["problems"]))
        events = [entry["payload"]["event"] for entry in logs["participant"] if entry["kind"] == "turn"]
        result = gp.participant_trace(events, store.artifact(info["encounter_id"]), info["arrival"], boundary_request=info.get("exit") == gp.EXIT_DEFINITIVE_REQUEST)
        if result.get("ok"):
            store.write_trace(info["encounter_id"], {"encounter_id": info["encounter_id"], "trace_digest": result["trace_digest"], "exit": info["exit"], "exit_minute": info["exit_minute"],
                                                     "trace": _plain(result["trace"])})
        result = gp.bounded_trace(result, info["exit"], info["exit_minute"])
    except Exception as error:
        LOG.warning("pilot closing trace unavailable: %s", error)
        result = {"ok": False, "problems": [str(error)], "blocks": []}
    closing = {"encounter_id": info["encounter_id"], "ok": bool(result.get("ok")), "blocks": result.get("blocks") or [], "exit": info.get("exit")}
    st.session_state[ENDED_KEY] = closing
    if not closing["ok"]:
        LOG.warning("pilot trace withheld: %s", "; ".join(result.get("problems") or []))
    return closing


def post_encounter(st: Any) -> None:
    """The page after a pilot encounter: the exit, then the faculty-reviewed management trace -- or, when it does not verify, nothing but the note that it is withheld."""
    info = session(st)
    if info is None:
        return
    closing = _closing(st)
    st.subheader("Development encounter ended")
    st.warning(gp.EXIT_MESSAGES.get(closing.get("exit") or "", gp.FINISHED_MESSAGE))
    if not closing["ok"]:
        st.info(gp.TRACE_WITHHELD)
        return
    st.subheader("Your management trace")
    st.caption(gp.TRACE_INTRO)
    for block in closing["blocks"]:
        if block.get("boundary"):
            st.warning("\n\n".join(f"**{line['label']}.** {line['text']}" for line in block["lines"]))
            continue
        with st.container(border=True):
            st.markdown(f"**Step {block['n']} · {block['minutes']}**")
            for line in block["lines"]:
                st.markdown(f"**{line['label']}:** {line['text']}")
            rows = [row for row in _step_orders(closing, block)]
            if rows:
                st.caption("What the simulator did with each order: " + " · ".join(rows))


def _step_orders(closing: dict, block: dict) -> list:
    return [str(text) for text in block.get("order_words") or ()]


# -- the faculty supervision page ----------------------------------------------------------------------------------------------------------

def supervision(st: Any, context: Any) -> None:
    """Faculty and administrators only: every pilot encounter of this deployment, and the five controls. Reads the pilot record; never the participant's session."""
    user = dict((context or {}).get("user") or {})
    if user.get("role") not in gp.FACULTY_ROLES or user.get("id") is None:
        st.error(UNAVAILABLE)
        return
    me = gp.faculty_ref(user["id"])
    st.title(SUPERVISION_TITLE)
    st.caption(f"{gp.PILOT_ID} · {gp.RATIFIED_CONSTRUCT} {gp.RATIFIED_STATUS} · development only · no scores · faculty interpretations stay faculty-only")
    try:
        store = _store()
        ids = store.ids()
    except Exception as error:
        st.error(f"The pilot record cannot be read ({type(error).__name__}): no encounter can be supervised.")
        return
    if st.button("Refresh", key="gi_pilot_refresh"):
        st.rerun()
    if not ids:
        st.info("No pilot encounter yet.")
        return
    statuses = {}
    for eid in ids:
        try:
            statuses[eid] = store.status(eid)
        except Exception as error:
            statuses[eid] = {"encounter_id": eid, "state": "RECORD_PROBLEM", "problems": [str(error)]}
    st.dataframe([{key: value for key, value in row.items() if key in ("encounter_id", "participant", "case_id", "state", "exit", "turns", "minute", "stop_requested", "unusable", "flags")}
                  for row in statuses.values()], use_container_width=True, hide_index=True)
    eid = st.selectbox("Encounter", ids, index=len(ids) - 1, key="gi_pilot_choice")
    row = statuses[eid]
    st.subheader(f"{eid} · {row.get('state')}")
    if row.get("problems"):
        st.error("Record problem: " + "; ".join(row["problems"]))
    logs = store.logs(eid)
    turns = [entry for entry in logs["participant"] if entry["kind"] == "turn"]
    with st.expander("Observe: turns as recorded", expanded=True):
        for entry in turns:
            event = entry["payload"]["event"]
            st.markdown(f"**minute {entry['payload'].get('minute')}** · BP {(entry['payload'].get('pressure') or {}).get('sbp')}/{(entry['payload'].get('pressure') or {}).get('dbp')} · "
                        f"{str(event.get('learner_input') or '').splitlines()[0][:300]}")
        ended = [entry for entry in logs["participant"] if entry["kind"] in ("ended", "interrupted", "left")]
        for entry in ended:
            st.write(f"{entry['kind']}: {json.dumps(entry['payload'], default=str)[:400]}")
    stop_col, unusable_col = st.columns(2)
    if row.get("state") == "ACTIVE" and not row.get("stop_requested"):
        if stop_col.button("Stop this encounter", key=f"gi_pilot_stop_{eid}"):
            store.append_faculty(eid, me, "stop", {"why": "stopped by the supervising faculty member"})
            st.success("Stop recorded: the encounter ends at the participant's next action or refresh.")
    elif row.get("stop_requested"):
        stop_col.caption("Stop already recorded.")
    reason = unusable_col.text_input("Why is this encounter unusable?", key=f"gi_pilot_unusable_reason_{eid}")
    if unusable_col.button("Mark unusable", key=f"gi_pilot_unusable_{eid}", disabled=not reason.strip()):
        store.append_faculty(eid, me, "unusable", {"reason": reason.strip()})
        st.success("Marked unusable.")
    with st.expander("Flag an output as unsafe or ambiguous", expanded=False):
        category = st.radio("Category", list(gp.FLAG_CATEGORIES), key=f"gi_pilot_flag_cat_{eid}", horizontal=True)
        where = st.text_input("Where (step, minute or screen)", key=f"gi_pilot_flag_where_{eid}")
        note = st.text_area("What is unsafe or ambiguous (synthetic case: no real-patient data)", key=f"gi_pilot_flag_note_{eid}")
        if st.button("Record the flag", key=f"gi_pilot_flag_{eid}", disabled=not note.strip()):
            store.append_faculty(eid, me, "flag", {"category": category, "where": where.strip(), "note": note.strip()})
            st.success("Flag recorded.")
    if st.button("Review the replay", key=f"gi_pilot_replay_{eid}"):
        review = gp.replay_review(store, eid, layer())
        store.append_faculty(eid, me, "replay_review", review)
        (st.success if review["usable"] else st.error)("Replay: " + ("every check matches" if review["usable"] else "NOT usable for analysis"))
        st.json(review["checks"])
    if st.button("Inspect the trace", key=f"gi_pilot_inspect_{eid}"):
        meta = store.meta(eid)
        result = gp.participant_trace([entry["payload"]["event"] for entry in turns], store.artifact(eid), meta.get("arrival") or {})
        store.append_faculty(eid, me, "inspect_trace", {"ok": bool(result.get("ok")), "problems": list(result.get("problems") or [])})
        if not result.get("ok"):
            st.error("The trace does not verify: " + "; ".join(result.get("problems") or []))
        for block in result.get("blocks") or ():
            st.markdown(f"**{('Step ' + str(block['n'])) if block.get('n') else 'Boundary'} · {block['minutes']}**")
            for line in block["lines"]:
                st.markdown(f"- *{line['label']}* ({line['provenance']}): {line['text']}")
        with st.expander("Structured trace and configuration (faculty only)", expanded=False):
            st.json({"configuration": meta.get("configuration"), "trace": result.get("trace")})
    flags = [entry for entry in logs["faculty"] if entry["action"] in ("flag", "unusable", "stop")]
    if flags:
        st.caption("Faculty record: " + " · ".join(f"{entry['action']} ({entry['faculty']})" for entry in flags))
