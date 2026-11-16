"""UX-003 to UX-009: the FACULTY TRAJECTORY REVIEW page (draws and records; decides nothing).

One page per scenario, in this order: context, timeline of interventions, trajectory, five blind questions, ONE button that locks the first impression and reveals the legacy comparator, the post-reveal
questions, ONE submit that moves on to the next scenario. The reviewer types no identifier, opens no file, picks no menu path and leaves nothing by a special route.

REACHABLE ONLY from the faculty review launcher, i.e. inside a process that named the review mode and for a faculty or administrator account (the page gate has already stopped everybody else). It checks the
role again here. It imports nothing of the Phase-3 layer, the engine or the common core: the page hands it the review layer (``layer.review``, ``layer.bundles``) and it draws what ``faculty_trajectory_review``
returns. The legacy comparator is built only from a LOCKED state, and until then no legacy number is in any element sent to the browser (not in a table, not in the chart data).
"""
from __future__ import annotations

import logging
from typing import Any

import faculty_trajectory_review as ftr

LOG = logging.getLogger("faculty_trajectory_review")      # what only the person who runs the environment needs: the technical reasons never reach the reviewer's screen

VIEW_KEY, SET_KEY, KEPT_KEY, FLASH_KEY = "ftr_view", "ftr_review_set", "ftr_bundles_kept", "ftr_flash"
SUMMARY_VIEW = "summary"
GENERIC_REFUSAL = "This is a faculty review environment. It is not available to this account."
COMMON_NAME, LEGACY_NAME = "Common authority", "Legacy comparator"
VARIABLES = ("SBP", "MAP", "DBP")
COLORS = {"SBP": "#0072B2", "MAP": "#D55E00", "DBP": "#009E73"}    # validated for light and dark surfaces, adjacent-pair CVD safe (dataviz skill, validate_palette)
STOP_NOTES = {
    "COLLAPSE_BOUNDARY": "The experiment stops here: the next interval would reach a patient state the pressure model cannot represent. This is an operational stop of the development environment, not an outcome of the patient.",
    "UNSUPPORTED_ACTION": "The experiment stops here: the last order is an action the pressure model does not represent. This is an operational stop of the development environment, not an outcome of the patient.",
}
STOP_NOTE_DEFAULT = "The experiment stops here. This is an operational stop of the development environment, not an outcome of the patient."


# -- the trajectory chart ---------------------------------------------------------------------------------------------------------------------------------------------
def _long(points: list, source: str) -> list:
    return [{"minute": point["minute"], "variable": name, "mmHg": point[key], "source": source} for point in points for name, key in (("SBP", "sbp"), ("MAP", "map"), ("DBP", "dbp"))]


def interventions(rows: list) -> list:
    """The numbered intervention markers of a timeline: rows that did something, grouped by the minute they were given (so two orders at one minute show as one marker, ``1,2``)."""
    by_minute: dict = {}
    for row in rows:
        if row["executed"] and row["intervention"] and row["minute"] is not None:
            by_minute.setdefault(int(row["minute"]), []).append(str(row["n"]))
    return [{"minute": minute, "label": ",".join(numbers)} for minute, numbers in sorted(by_minute.items())]


def pressure_chart(common: list, legacy: list | None, markers: list, stop_minute: int | None, *, common_name: str = COMMON_NAME):
    """Common trajectory (solid) and, only when handed in, the legacy comparator (dashed) on the SAME axes; intervention markers drawn once. Colour follows the variable, dash follows the series.
    ``common_name`` is the series name the tooltip shows (the re-review has no comparator and no authority behind its trajectory, so it passes a neutral one)."""
    import altair as alt
    data = _long(common, common_name) + (_long(legacy, LEGACY_NAME) if legacy else [])
    x_max = max([point["minute"] for point in common] + ([int(stop_minute)] if stop_minute else []) + [10]) * 1.04
    x = alt.X("minute:Q", title="Minutes since arrival", scale=alt.Scale(domain=[0, x_max], nice=False), axis=alt.Axis(tickCount=7, format="d"))
    y = alt.Y("mmHg:Q", title="mmHg", scale=alt.Scale(domain=[0, 140]))
    color = alt.Color("variable:N", scale=alt.Scale(domain=list(VARIABLES), range=[COLORS[name] for name in VARIABLES]), legend=alt.Legend(title=None, orient="top"))
    tooltip = [alt.Tooltip("variable:N", title="Variable"), alt.Tooltip("minute:Q", title="Minute"), alt.Tooltip("mmHg:Q", title="mmHg"), alt.Tooltip("source:N", title="Series")]
    base = alt.Chart(alt.Data(values=data))
    encodings = dict(x=x, y=y, color=color, tooltip=tooltip)
    if legacy:
        encodings["strokeDash"] = alt.StrokeDash("source:N", scale=alt.Scale(domain=[common_name, LEGACY_NAME], range=[[1, 0], [6, 4]]), legend=alt.Legend(title=None, orient="top"))
        point_shape = alt.Shape("source:N", scale=alt.Scale(domain=[common_name, LEGACY_NAME], range=["circle", "diamond"]), legend=None)
        points = base.mark_point(filled=True, size=55).encode(**{**encodings, "shape": point_shape})
    else:
        points = base.mark_point(filled=True, size=55, shape="circle").encode(**encodings)
    layers = [base.mark_line(strokeWidth=2).encode(**encodings), points]
    if markers:
        guide = alt.Chart(alt.Data(values=markers))
        layers += [guide.mark_rule(strokeDash=[2, 3], color="#8a8a8a", strokeWidth=1).encode(x="minute:Q"),
                   guide.mark_text(baseline="top", align="center", dy=2, color="#8a8a8a", fontSize=12).encode(x="minute:Q", y=alt.value(2), text="label:N")]
    if stop_minute:
        stop = alt.Chart(alt.Data(values=[{"minute": int(stop_minute), "label": "Stop"}]))
        layers += [stop.mark_rule(color="#6b6b6b", strokeWidth=2).encode(x="minute:Q"),
                   stop.mark_text(baseline="top", align="left", dx=4, dy=18, color="#6b6b6b", fontSize=12).encode(x="minute:Q", y=alt.value(2), text="label:N")]
    return alt.layer(*layers).properties(height=320)


def vital_chart(rows: list, key: str, title: str):
    import altair as alt
    data = [{"minute": row["minute"], "value": row[key]} for row in rows if row.get(key) is not None]
    base = alt.Chart(alt.Data(values=data)).encode(x=alt.X("minute:Q", title="Minutes since arrival", scale=alt.Scale(nice=False)), y=alt.Y("value:Q", title=title, scale=alt.Scale(zero=False)),
                                                     tooltip=[alt.Tooltip("minute:Q", title="Minute"), alt.Tooltip("value:Q", title=title)])
    return (base.mark_line(strokeWidth=2, color="#6b7280") + base.mark_point(filled=True, size=45, color="#6b7280")).properties(height=150)


# -- small helpers ----------------------------------------------------------------------------------------------------------------------------------------------------
def _signal(st: Any, kind: str, text: str) -> None:
    getattr(st, kind)(text)


def _arrival_line(arrival: dict) -> str:
    parts = [f"BP {arrival['sbp']}/{arrival['dbp']} mmHg", f"HR {arrival['hr']}/min", f"SpO₂ {arrival['spo2']}%", f"RR {arrival['rr']}/min", f"capillary refill {arrival['crt']} s"]
    return "On arrival: " + " · ".join(part for part in parts if "None" not in part) + "."


def _stop_note(view: dict, item: dict) -> str:
    stop_class = str(dict(dict(item["bundle"]).get("authority_view") or {}).get("stop_class") or "")
    return STOP_NOTES.get(stop_class, STOP_NOTE_DEFAULT)


def _timeline_table(st: Any, view: dict, item: dict) -> None:
    rows = [{"#": row["n"], "Minute": row["minute"], "What was done": row["action"], "What the encounter did": row["result"]} for row in view["timeline"]]
    script = [step for step in item.get("script") or ()]
    if view["halted"] and len(script) > len(rows):                          # the order that was in progress when the experiment stopped is not in the executed timeline: show it
        stopped = script[len(rows)]
        text = stopped[1] if stopped[1] else ("Ask the patient a question" if stopped[0] == "question" else "Examine the patient")
        last = view["timeline"][-1] if view["timeline"] else None
        given_at = (int(last["minute"] or 0) + int(last["advance"] or 0)) if last else 0          # the minute the stopped order would have been given (the stop line of the chart is where the experiment halts)
        rows.append({"#": len(rows) + 1, "Minute": given_at, "What was done": text, "What the encounter did": "Not executed: the experiment stopped here"})
    st.dataframe(rows, hide_index=True, width="stretch")


def _vitals_panel(st: Any, view: dict) -> None:
    rows = view["context_vitals"]
    with st.expander("Heart rate and capillary refill as shown during the encounter", expanded=False):
        st.caption("Context for your interpretation. These two variables are not part of the pressure trajectory you are judging.")
        if len([row for row in rows if row.get("hr") is not None]) < 2:
            st.write("Only the arrival values exist for this scenario: " + _arrival_line(view["arrival"]))
            return
        left, right = st.columns(2)
        with left:
            st.caption("Heart rate (/min)")
            st.altair_chart(vital_chart(rows, "hr", "Heart rate (/min)"), width="stretch")
        with right:
            st.caption("Capillary refill (s)")
            st.altair_chart(vital_chart(rows, "crt", "Capillary refill (s)"), width="stretch")


def _choice(st: Any, key: str, label: str, choices: list, saved: str | None, on_change: Any, args: tuple, disabled: bool = False) -> str | None:
    """A radio group whose answer is saved by a CALLBACK, which Streamlit runs only for the widget the reviewer actually changed and BEFORE the page body: a stale widget in another tab can never overwrite a
    newer saved answer, and an edit made in the same run as a navigation click is saved first."""
    index = choices.index(saved) if saved in choices else None
    return st.radio(label, choices, index=index, horizontal=True, key=key, disabled=disabled, on_change=on_change, args=args)


def _flash(st: Any, text: str) -> None:
    st.session_state[FLASH_KEY] = text


def _on_answer(st: Any, log: ftr.ReviewLog, question_id: str, key: str) -> None:
    value = st.session_state.get(key)
    if value is None:
        return
    try:
        outcome = log.answer(question_id, value)
    except Exception:                                                        # whatever happens, the browser never gets a traceback with a path
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    if not outcome["ok"]:
        _flash(st, outcome["why"])


def _on_overall(st: Any, log: ftr.ReviewLog, key: str) -> None:
    value = st.session_state.get(key)
    if value is None:
        return
    try:
        outcome = log.set_overall(value)
    except Exception:
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    if not outcome["ok"]:
        _flash(st, outcome["why"])


def _on_comment(st: Any, log: ftr.ReviewLog, key: str, after_reveal: bool) -> None:
    text = st.session_state.get(key) or ""
    try:
        outcome = log.comment(text, after_reveal=after_reveal)
    except Exception:
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    st.session_state[key + "__refusal"] = None if outcome["ok"] else outcome["why"]


def _unsaved_comment(st: Any, key: str, text: str, saved: str) -> None:
    """A comment that was refused stays in its box and is SAID to be unsaved, for as long as it differs from what is saved (it is never lost in silence)."""
    reason = st.session_state.get(key + "__refusal")
    if reason and text != saved:
        st.warning("This comment is not saved yet: " + reason + ". Rewrite it (for example, give numbers with their units: 'MAP about 65 to 75 mmHg').")


def _header(st: Any, prog: dict, order: list, sid: str) -> None:
    """Progress and the estimated time left (an author's estimate, labelled as such)."""
    entry = next(item for item in order if item["scenario_id"] == sid)
    required = [item for item in order if item["required"]]
    if entry["required"]:
        position = [item["scenario_id"] for item in required].index(sid) + 1
        label = f"Scenario {position} of {len(required)}"
    else:
        optional = [item for item in order if not item["required"]]
        label = f"Optional scenario {[item['scenario_id'] for item in optional].index(sid) + 1} of {len(optional)}"
    st.progress(min(1.0, len([i for i in prog["submitted"] if i in prog["required"]]) / max(1, len(prog["required"]))))
    st.caption(f"{label} · {len([i for i in prog['submitted'] if i in prog['required']])} of {len(prog['required'])} required scenarios reviewed · "
               f"estimated time remaining ≈ {prog['estimated_minutes_left']} min (an estimate, not a measurement)")


def _navigation(st: Any, order: list, prog: dict, view: str) -> None:
    columns = st.columns(len(order) + (1 if prog["required_done"] else 0))
    for column, entry in zip(columns, order):
        identifier, status = entry["scenario_id"], prog["statuses"][entry["scenario_id"]]
        label = ("✓ " if status == "SUBMITTED" else "") + identifier + ("" if entry["required"] else " (optional)")
        allowed = status == "SUBMITTED" or identifier in prog["enterable"]
        if column.button(label, key=f"ftr_nav_{identifier}", disabled=not allowed, type="primary" if identifier == view else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = identifier
            st.rerun()
    if prog["required_done"]:
        if columns[-1].button("Summary", key="ftr_nav_summary", type="primary" if view == SUMMARY_VIEW else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = SUMMARY_VIEW
            st.rerun()


# -- one scenario -----------------------------------------------------------------------------------------------------------------------------------------------------
def _scenario(st: Any, item: dict, log: ftr.ReviewLog, bundles: Any, last: bool) -> None:
    state = log.state()
    sid = item["scenario_id"]
    flash = st.session_state.pop(FLASH_KEY, None)
    if flash:
        st.error("Not saved: " + str(flash))
    if state["status"] == "UNREADABLE":
        st.error("The saved answers for this scenario cannot be read, so nothing more is recorded for it. Tell the person who runs this environment.")
        LOG.warning("unreadable review log for %s", sid)
        return
    view = ftr.blind_view(item)
    st.subheader(f"{view['title']}")
    st.markdown("**Clinical context.** " + view["context"] + " " + _arrival_line(view["arrival"]))
    st.caption("What to judge here: " + view["purpose"])
    st.markdown("**What was done**")
    _timeline_table(st, view, item)
    markers = interventions(view["timeline"])
    if view["halted"]:
        st.info(_stop_note(view, item))
    submitted, locked = state["submitted"], state["locked"]
    if not locked:
        st.markdown("**Trajectory under review** · solid lines; numbers mark the interventions in the table")
        st.altair_chart(pressure_chart(view["common"], None, markers, view["stop_minute"]), width="stretch")
        _vitals_panel(st, view)
    else:
        try:
            comparison = ftr.comparator_view(item, state)
        except ftr.Locked:
            st.error("The comparison is not available yet.")
            return
        st.markdown(f"**{COMMON_NAME} (solid lines) vs {comparison['label']} (dashed lines)** · same axes; numbers mark the interventions in the table")
        st.altair_chart(pressure_chart(view["common"], comparison["legacy"], markers, view["stop_minute"]), width="stretch")
        st.caption(comparison["note"])
        with st.expander("Values at each minute (common minus legacy, mmHg)", expanded=False):
            st.dataframe([{"Minute": row["minute"], "SBP": row["sbp"], "DBP": row["dbp"], "MAP": row["map"]} for row in comparison["differences"]], hide_index=True, width="stretch")
        _vitals_panel(st, view)

    # ---- first impression (blind): saved by callbacks as it is given
    if not locked:
        st.markdown("**Your first impression** · answer before the comparator is revealed")
        for question in view["questions"]:
            key = f"ftr_{sid}_{question['id']}"
            _choice(st, key, f"{question['id']} · {question['topic']}: {question['text']}", question["choices"], state["blind"].get(question["id"]), _on_answer, (st, log, question["id"], key))
        key = f"ftr_{sid}_comment"
        comment = st.text_area("Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)", value=state["blind_comment"], key=key, max_chars=ftr.MAX_COMMENT,
                               on_change=_on_comment, args=(st, log, key, False))
        _unsaved_comment(st, key, comment, state["blind_comment"])
        _, required = ftr.required_questions(item)
        ready = all(question in state["blind"] for question in required)
        if not ready:
            st.caption("Answer every question above to enable the next step. Your answers are saved as you go; once you lock them they cannot be changed.")
        if st.button("LOCK FIRST IMPRESSION & REVEAL COMPARATOR", type="primary", disabled=not ready, key=f"ftr_{sid}_lock"):
            outcome = log.lock()
            if not outcome["ok"]:
                st.error(outcome["why"])
            else:
                st.rerun()
        return

    # ---- locked: the first impression is fixed
    with st.expander("Your first impression (locked)", expanded=False):
        for question in view["questions"]:
            st.write(f"{question['topic'].title()}: **{(state['locked_answers'] or {}).get(question['id'], '—')}**")
        if state["locked_comment"]:
            st.write("Comment: " + state["locked_comment"])
        st.caption(f"Locked at {state['locked_at']}")
    if submitted:
        st.success("This scenario is submitted. It is shown read-only.")
        st.write(f"Did seeing the legacy comparator change your judgment? **{state['post'].get('R1', '—')}**")
        if state["after_reveal_comment"]:
            st.write("After reveal: " + state["after_reveal_comment"])
        st.write(f"Overall: **{state['overall']}**")
        return
    st.markdown("**After seeing the comparator**")
    key = f"ftr_{sid}_R1"
    _choice(st, key, ftr.CHANGED["text"], list(ftr.CHANGED["choices"]), state["post"].get("R1"), _on_answer, (st, log, "R1", key))
    key = f"ftr_{sid}_after"
    after = st.text_area("Optional comment after the reveal", value=state["after_reveal_comment"], key=key, max_chars=ftr.MAX_COMMENT, on_change=_on_comment, args=(st, log, key, True))
    _unsaved_comment(st, key, after, state["after_reveal_comment"])
    key = f"ftr_{sid}_overall"
    _choice(st, key, "Overall judgment of this trajectory", list(ftr.OVERALL), state["overall"], _on_overall, (st, log, key))
    ready = bool(state["post"].get("R1") and state["overall"])
    if st.button("Submit and finish" if last else "Submit and continue to the next scenario", type="primary", disabled=not ready, key=f"ftr_{sid}_submit"):
        result = log.submit()
        if result.get("ok") or result.get("record_id"):
            st.session_state[VIEW_KEY] = None
            st.rerun()
        else:
            st.error("Your review could not be saved, so nothing moved on: " + str(result.get("why") or "unknown problem") + ".")


# -- summary ----------------------------------------------------------------------------------------------------------------------------------------------------------
def _summary(st: Any, root: Any, reviewer: str, items: dict, order: list, digest: str, prog: dict, bundles: Any) -> None:
    summary = ftr.summarize(root, reviewer, items, order, digest, bundles=bundles)
    written = ftr.write_summary(root, summary)
    reviewed_required = summary["required_reviewed"]
    if summary["complete"]:
        st.success(f"REVIEW COMPLETE · {reviewed_required}/{len(summary['required_scenarios'])} required scenarios reviewed")
    else:
        st.warning(f"{reviewed_required}/{len(summary['required_scenarios'])} required scenarios reviewed so far")
    counts = summary["judgments"]
    if summary["optional_reviewed"]:
        st.caption(f"The counts include {summary['optional_reviewed']} optional scenario(s) beyond the {len(summary['required_scenarios'])} required.")
    columns = st.columns(4)
    for column, (choice, label) in zip(columns, (("ACCEPT", "Accept"), ("ACCEPT_WITH_LIMITATION", "Accept with limitation"), ("RECALIBRATE", "Recalibrate"), ("REJECT", "Reject"))):
        column.metric(label, counts[choice])
    st.dataframe([{"Scenario": row["scenario_id"], "Title": row["title"], "Overall": row["overall"], "Comparator changed your judgment": (row["changed_judgment"] or "").split(" — ")[0] if row["changed_judgment"] else "—"}
                  for row in summary["scenarios"]], hide_index=True, width="stretch")
    st.markdown("**Comments to follow up**")
    if summary["comments"]:
        for comment in summary["comments"]:
            st.write(f"{comment['scenario_id']} ({comment['overall']}, {comment['stage']}): {comment['text']}")
    else:
        st.write("No comments were written.")
    optional = [entry["scenario_id"] for entry in order if not entry["required"] and prog["statuses"][entry["scenario_id"]] != "SUBMITTED"]
    if optional and summary["complete"]:
        st.markdown("**Optional scenarios** (not required)")
        for identifier in optional:
            title = items[identifier]["title"]
            if st.button(f"Review optional scenario {identifier} · {title}", key=f"ftr_opt_{identifier}"):
                st.session_state[VIEW_KEY] = identifier
                st.rerun()
    if written["written"]:
        st.caption("The technical session summary was created automatically. The counts above are your own judgments, tabulated; they are not a score and not a clinical validation.")
    else:
        st.error("The technical session summary could not be written. Tell the person who runs this environment.")
    if summary["technical_problems"]:
        st.warning("A technical check found something the person who runs this environment should look at. The scenarios it concerns are not counted above.")
        LOG.warning("review summary technical problems: %s", "; ".join(summary["technical_problems"]))


# -- entry ------------------------------------------------------------------------------------------------------------------------------------------------------------
def draw(st: Any, layer: Any, context: Any) -> None:
    """The whole trajectory review: header, navigation and the scenario (or the summary). Faculty/administrator accounts only; the page that calls it has already passed the review gate."""
    review, bundles = layer.review, layer.bundles
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        st.error(GENERIC_REFUSAL)
        return
    root = review.review_root()
    if root is None:
        st.error("The review cannot run: no review store is configured.")
        return
    loaded = st.session_state.get(SET_KEY)
    if loaded is None:
        loaded = ftr.load_set(bundles=bundles, scenario_of=review.scenario)
        st.session_state[SET_KEY] = loaded
    if not loaded["ok"]:
        st.error("The stored trajectories cannot be verified, so no review can start. Tell the person who runs this environment.")
        LOG.warning("review set refused: %s", "; ".join(loaded["problems"]))
        return
    items, digest = loaded["items"], loaded["digest"]
    for problem in loaded["problems"]:                                      # a scenario that does not verify is simply not offered (the reasons go to the operator's log, not to the screen)
        st.caption("Not offered: " + problem.split(":")[0] + " (its stored trajectory could not be verified)")
        LOG.warning("scenario not offered: %s", problem)
    reviewer = ftr.reviewer_ref(user["id"])
    order = ftr.sequence(items)
    account = {"role": user.get("role")}
    logs = {entry["scenario_id"]: ftr.ReviewLog(root, reviewer, items[entry["scenario_id"]], set_digest=digest, bundles=bundles, account=account) for entry in order}
    if st.session_state.get(KEPT_KEY) != digest:                           # the packages the reviewer is shown are kept in the reviewer's own store (idempotent, create-only), once per session
        for entry in order:
            if not bundles.write(items[entry["scenario_id"]]["bundle"]).get("stored"):
                st.error("The review cannot run: the stored trajectory could not be kept in the review store.")
                return
        st.session_state[KEPT_KEY] = digest
    prog = ftr.progress(logs, order)
    st.header("Faculty Trajectory Review")
    view = st.session_state.get(VIEW_KEY)
    if not isinstance(view, str):
        view = None
    if view == SUMMARY_VIEW and prog["required_done"]:
        pass
    elif view not in prog["enterable"]:
        view = SUMMARY_VIEW if (prog["required_done"] and (prog["all_done"] or view is None)) else prog["current"]
    if view is None:
        view = SUMMARY_VIEW
    _navigation(st, order, prog, view)
    if view == SUMMARY_VIEW:
        _summary(st, root, reviewer, items, order, digest, prog, bundles)
        return
    _header(st, prog, order, view)
    current = next(entry for entry in order if entry["scenario_id"] == view)
    _scenario(st, items[view], logs[view], bundles, last=(not current["required"]) or prog["remaining_required"] <= 1)
