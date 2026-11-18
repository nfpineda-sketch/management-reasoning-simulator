"""P3-406 to P3-409: the MULTIFAMILY TONE REVIEW page (draws and records; decides nothing).

The same page the faculty trajectory review and the re-review have -- it REUSES their chart, intervention table, answer widgets and autosave callbacks -- for the multifamily tone set: one scenario at a time, in this
order: what you are judging, clinical context, the one intervention, the pressure trajectory, five questions, an optional comment, ONE button that LOCKS the first impression, the overall judgment with an optional
comment, ONE submit that moves on to the next scenario, and a completion screen after the last. No comparator exists here: there is no reveal step, no legacy number, no earlier trajectory and no other set; no other
setting of the response and no mechanism exists in a scenario's view.

TWO SEPARATE SCREENS COME AFTER THE FIFTH SUBMIT, never before: the SUMMARY (``REVIEW COMPLETE`` and the limitations that the review cannot judge, drawn only here) and the OPTIONAL SENSITIVITY check (the other settings of
the response on the same axes, with one question per scenario). The main review is complete without the second one.

REACHABLE ONLY from the faculty review launcher, i.e. inside a process that named the review mode and for a faculty or administrator account (the page gate has already stopped everybody else); it checks the role again
here. It imports nothing of the Phase-3 layer, the engine or the common core. The page shows clinical content only: the audit metadata and the sources never reach it (``ftm.load_set`` hands them apart, and only the record
writer uses them), and nothing is cached in the session.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import faculty_trajectory_review as ftr
import faculty_trajectory_review_ui as tui
import faculty_tone_review as ftm

LOG = logging.getLogger("faculty_tone_review")       # what only the person who runs the environment needs: the technical reasons never reach the reviewer's screen
VIEW_KEY = "tn_view"          # its own session keys and widget keys: the other reviews' pages and this one never share state
RESYNC_KEY, NOTICE_KEY = "tn_resync", "tn_notice"
SUMMARY_VIEW, SENSITIVITY_VIEW = "summary", "sensitivity"
#: The operator's own switch (a process environment variable, like the other review flags; never the Secrets file). ``off`` opens the other review modes while this review is incomplete, for the operator who needs them
#: (and for the tests of those modes). Left out, the other modes are held until this reviewer's five scenarios are submitted and verified.
OPERATOR_FLAG, OPERATOR_OPEN = "MRS_FACULTY_TONE_GATE", "off"
GENERIC_REFUSAL = tui.GENERIC_REFUSAL
LOCK_LABEL, NEXT_LABEL, FINISH_LABEL = "LOCK FIRST IMPRESSION", "SUBMIT & NEXT", "SUBMIT & FINISH"
JUDGING_LABEL = "What you are judging"
SERIES_NAME = "Trajectory under review"       # the series name the chart tooltip shows: neutral (no authority and no comparator stand behind this review's trajectory)
PRESSURE_ONLY_NOTE = ("Heart rate and capillary refill are intentionally not displayed in this pressure-trajectory review: they were not recomputed for these trajectories.")
LIMITATIONS_HEADING = "DEVELOPMENT LIMITATIONS TO FOLLOW UP"
OPTIONAL_NOTE = ("Optional. Your judgments above are complete and locked, and nothing here changes them. For each scenario where the strength of the vascular response materially changes the picture, the same order "
                 "is drawn at three settings on the same axes. No parameter values are shown.")
SERIES = {"LOW": {"dash": [2, 3], "shape": "triangle-down"}, "CENTER": {"dash": [1, 0], "shape": "circle"}, "HIGH": {"dash": [7, 3], "shape": "diamond"}}
MAP_COLOR = tui.COLORS["MAP"]


def _on_overall_comment(st: Any, log: ftm.ToneReviewLog, key: str) -> None:
    text = st.session_state.get(key) or ""
    try:
        outcome = log.overall_comment(text)
    except Exception:                                                        # whatever happens, the browser never gets a traceback with a path
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    st.session_state[key + "__refusal"] = None if outcome["ok"] else outcome["why"]


def _on_envelope(st: Any, log: ftm.SensitivityLog, scenario_id: str, key: str) -> None:
    value = st.session_state.get(key)
    if value is None:
        return
    try:
        outcome = log.set_envelope(scenario_id, value)
    except Exception:
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    if not outcome["ok"]:
        tui._flash(st, outcome["why"])


def _on_note(st: Any, log: ftm.SensitivityLog, scenario_id: str, key: str) -> None:
    text = st.session_state.get(key) or ""
    try:
        outcome = log.set_note(scenario_id, text)
    except Exception:
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    st.session_state[key + "__refusal"] = None if outcome["ok"] else outcome["why"]


def _header(st: Any, prog: dict, order: list, sid: str) -> None:
    position = [entry["scenario_id"] for entry in order].index(sid) + 1
    done = len(prog["submitted"])
    st.progress(min(1.0, done / max(1, len(order))))
    st.caption(f"Scenario {position} of {len(order)} · {done} of {len(order)} reviewed · estimated time remaining ≈ {prog['estimated_minutes_left']} min (an estimate, not a measurement)")


def _navigation(st: Any, items: dict, order: list, prog: dict, view: str, optional: bool) -> None:
    """``optional`` is True only when the review is complete AND verified and the optional check has something to show."""
    for number, (column, entry) in enumerate(zip(st.columns(len(order)), order), 1):
        identifier, status = entry["scenario_id"], prog["statuses"][entry["scenario_id"]]
        allowed = status == "SUBMITTED" or identifier in prog["enterable"]
        label = ("✓ " if status == "SUBMITTED" else "") + f"{number} · {items[identifier]['short']}"
        if column.button(label, key=f"tn_nav_{identifier}", disabled=not allowed, type="primary" if identifier == view else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = identifier
            st.rerun()
    if prog["required_done"]:                                           # a second, shorter row: seven buttons on one row would truncate the scenario names
        columns = st.columns([1, 1, 3] if optional else [1, 4])
        if columns[0].button("Summary", key="tn_nav_summary", type="primary" if view == SUMMARY_VIEW else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = SUMMARY_VIEW
            st.rerun()
        if optional and columns[1].button("Sensitivity (optional)", key="tn_nav_sensitivity", type="primary" if view == SENSITIVITY_VIEW else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = SENSITIVITY_VIEW
            st.rerun()


def _arrival_line(arrival: dict) -> str:
    """The arrival of an authored case as the reviewer is shown it: pressure, oxygen saturation and respiratory rate. No heart rate and no capillary refill."""
    parts = [f"BP {arrival['sbp']}/{arrival['dbp']} mmHg (MAP {arrival['map']})", f"SpO₂ {arrival['spo2']}%", f"RR {arrival['rr']}/min"]
    return "On arrival: " + " · ".join(parts) + "."


def _values_table(st: Any, item: dict) -> None:
    st.dataframe([{"Minute": row["minute"], "SBP": row["sbp"], "DBP": row["dbp"], "MAP": row["map"]} for row in ftm.values_table(item)], hide_index=True, width="stretch")
    st.caption("SBP, DBP and MAP (mmHg) at the minutes listed are the trajectory you are judging; the graph shows every minute. " + PRESSURE_ONLY_NOTE)


def other_modes_held(st: Any, layer: Any, context: Any) -> bool:
    """True while this reviewer has not completed this review, i.e. while the launcher must offer nothing but it: the first review, the re-review and the live encounter draw earlier trajectories, the legacy comparator,
    heart rate and capillary refill and the reviewer's earlier judgments, none of which may be reachable from the blind first pass. Complete means the summary counts all five scenarios, which it does only for records that
    verify against the log that closed them: a forged log does not release the hold. Whatever cannot be decided (no store, an unverifiable set, no faculty account) is HELD. The operator's switch releases it."""
    if os.environ.get(OPERATOR_FLAG, "").strip().lower() == OPERATOR_OPEN:
        return False
    review = layer.review
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        return True
    root = review.review_root()
    loaded = ftm.load_set()
    if root is None or not loaded["ok"]:
        return True
    return not _verified_summary(root, ftr.reviewer_ref(user["id"]), loaded, layer.bundles)["complete"]


def _verified_summary(root: Any, reviewer: str, loaded: dict, bundles: Any) -> dict:
    """The summary derived ONLY from records that verify against the logs that closed them: the one source of 'complete' for everything that depends on it (the limitations, the optional check, the other modes)."""
    offered = [entry["scenario_id"] for entry in loaded["sensitivity"] if entry["material"]]
    return ftm.summarize(root, reviewer, loaded["items"], ftm.sequence(loaded["items"]), loaded["digest"], loaded["audit"], loaded["limitations"], offered, bundles=bundles)


def _lock(st: Any, log: ftm.ToneReviewLog, sid: str, required: list, state: dict) -> None:
    """Lock the first impression ONLY if what this screen shows is what the log holds. The log is what is locked, so a screen that shows something else (another window of the same account changed an answer, or a comment
    the log refused is still in its box) must never lock behind the reviewer's back: the lock is irreversible."""
    stale = [question for question in required if st.session_state.get(f"tn_{sid}_{question}") != state["blind"].get(question)]
    comment_key = f"tn_{sid}_comment"
    differs = (st.session_state.get(comment_key) or "") != state["blind_comment"]
    if stale or differs:
        if not stale and st.session_state.get(comment_key + "__refusal"):
            st.error("The comment in the box is not saved (see the note under it). Rewrite it or clear it, then lock.")
            return
        st.session_state[RESYNC_KEY] = sid
        st.session_state[NOTICE_KEY] = "Nothing was locked: this screen was out of date (an answer was changed in another window). It has been reloaded from your saved answers: check them and lock again."
        st.rerun()
        return
    outcome = log.lock()
    if not outcome["ok"]:
        st.error(outcome["why"])
    else:
        st.rerun()


# -- one scenario -----------------------------------------------------------------------------------------------------------------------------------------------------
def _case_block(st: Any, view: dict) -> None:
    """The clinical context of the scenario: the label, the authored context and findings, and the baseline pressure. Nothing of the mechanism."""
    probe = view["kind"] == ftm.KIND_PROBE
    (st.warning if probe else st.caption)(f"**{view['banner']}** · {view['note']}" if probe else f"{view['banner']} · {view['note']}")
    st.subheader(view["title"])
    st.info(f"**{JUDGING_LABEL}.** {view['purpose']}")
    st.markdown("**Clinical context.** " + view["context"] + ("" if probe else " " + _arrival_line(view["arrival"])))
    st.markdown("**Baseline state**" if probe else "**Baseline findings (authored)**")
    st.markdown("\n".join(f"- {fact}" for fact in view["baseline_facts"]))


def _scenario(st: Any, item: dict, log: ftm.ToneReviewLog, last: bool) -> None:
    state = log.state()
    sid = item["scenario_id"]
    if st.session_state.get(RESYNC_KEY) == sid:                                  # a lock was refused because this screen showed answers the log no longer holds: the widgets are rebuilt from the log, before they are drawn
        for key in [key for key in list(st.session_state.keys()) if str(key).startswith(f"tn_{sid}_")]:
            st.session_state.pop(key, None)
        st.session_state.pop(RESYNC_KEY, None)
    flash = st.session_state.pop(tui.FLASH_KEY, None)
    if flash:
        st.error("Not saved: " + str(flash))
    notice = st.session_state.pop(NOTICE_KEY, None)
    if notice:
        st.warning(str(notice))
    if state["status"] == "UNREADABLE":
        st.error("The saved answers for this scenario cannot be read, so nothing more is recorded for it. Tell the person who runs this environment.")
        LOG.warning("unreadable tone review log for %s", sid)
        return
    view = ftm.blind_view(item)
    _case_block(st, view)
    st.markdown("**What was done**")
    tui._timeline_table(st, view, item)
    st.caption(view["intervention"])
    st.markdown("**Pressure trajectory** · solid lines; the number marks the intervention in the table")
    st.altair_chart(tui.pressure_chart(view["common"], None, tui.interventions(view["timeline"]), None, common_name=SERIES_NAME, y_max=ftm.y_axis_max(item),
                                       x_title="Minutes" if view["kind"] == ftm.KIND_PROBE else "Minutes since arrival"), width="stretch")
    _values_table(st, item)

    # ---- first impression: saved by callbacks as it is given, locked by ONE button
    if not state["locked"]:
        st.markdown("**Your first impression** · saved as you go; once you lock it, it cannot be changed")
        for question in view["questions"]:
            key = f"tn_{sid}_{question['id']}"
            tui._choice(st, key, f"{question['id']} · {question['topic']}: {question['text']}", question["choices"], state["blind"].get(question["id"]), tui._on_answer, (st, log, question["id"], key))
        key = f"tn_{sid}_comment"
        comment = st.text_area("Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)", value=state["blind_comment"], key=key, max_chars=ftr.MAX_COMMENT,
                               on_change=tui._on_comment, args=(st, log, key, False))
        tui._unsaved_comment(st, key, comment, state["blind_comment"])
        _, required = ftr.required_questions(item)
        ready = all(question in state["blind"] for question in required)
        if not ready:
            st.caption("Answer every question above to enable the lock.")
        if st.button(LOCK_LABEL, type="primary", disabled=not ready, key=f"tn_{sid}_lock"):
            _lock(st, log, sid, required, state)
        return

    # ---- locked: the first impression is fixed, then the overall judgment
    with st.expander("Your first impression (locked)", expanded=True):
        for question in view["questions"]:
            st.write(f"{question['topic'].title()}: **{(state['locked_answers'] or {}).get(question['id'], '—')}**")
        if state["locked_comment"]:
            st.write("Comment: " + state["locked_comment"])
        st.caption(f"Locked at {state['locked_at']}")
    if state["submitted"]:
        st.success("This scenario is submitted. It is shown read-only.")
        st.write(f"Overall: **{state['overall']}**")
        if state["overall_comment"]:
            st.write("Overall comment: " + state["overall_comment"])
        return
    st.markdown("**Overall judgment of this trajectory**")
    key = f"tn_{sid}_overall"
    tui._choice(st, key, "Overall judgment", list(ftr.OVERALL), state["overall"], tui._on_overall, (st, log, key))
    key = f"tn_{sid}_overall_comment"
    note = st.text_area("Optional overall comment", value=state["overall_comment"], key=key, max_chars=ftr.MAX_COMMENT, on_change=_on_overall_comment, args=(st, log, key))
    tui._unsaved_comment(st, key, note, state["overall_comment"])
    if st.button(FINISH_LABEL if last else NEXT_LABEL, type="primary", disabled=not state["overall"], key=f"tn_{sid}_submit"):
        if (st.session_state.get(key) or "") != state["overall_comment"]:       # a refused comment is still in its box: it must not be dropped in silence when the scenario closes
            st.error("The overall comment in the box is not saved (see the note under it). Rewrite it or clear it, then submit.")
            return
        result = log.submit()
        if result.get("ok") or result.get("record_id"):
            st.session_state[VIEW_KEY] = None
            st.rerun()
        else:
            st.error("Your review could not be saved, so nothing moved on: " + str(result.get("why") or "unknown problem") + ".")


# -- completion -------------------------------------------------------------------------------------------------------------------------------------------------------
def _summary(st: Any, root: Any, summary: dict, loaded: dict, order: list) -> None:
    items = loaded["items"]
    written = ftm.write_summary(root, summary)
    total, reviewed = len(order), len(summary["scenarios_reviewed"])
    if summary["complete"]:
        st.success(f"REVIEW COMPLETE · {reviewed} / {total}")
        st.write(ftm.COMPLETION_NOTE)
    else:
        st.warning(f"{reviewed} / {total} scenarios reviewed so far")
    columns = st.columns(4)
    for column, (choice, label) in zip(columns, (("ACCEPT", "Accept"), ("ACCEPT_WITH_LIMITATION", "Accept with limitation"), ("RECALIBRATE", "Recalibrate"), ("REJECT", "Reject"))):
        column.metric(label, summary["judgments"][choice])
    st.dataframe([{"Scenario": items[row["scenario_id"]]["short"], "Overall": row["overall"], **{question["id"]: row["first_pass"].get(question["id"], "—") for question in ftr.FIRST_PASS}}
                  for row in summary["scenarios"]], hide_index=True, width="stretch")
    if summary["complete"]:
        st.markdown(f"**{LIMITATIONS_HEADING}**")
        st.markdown("\n".join(f"- **{entry['id']}** · {entry['text']}" for entry in summary["limitations"]))
    st.markdown("**Comments to follow up**")
    if summary["comments"]:
        for comment in summary["comments"]:
            st.write(f"{items[comment['scenario_id']]['short']} ({comment['overall']}, {comment['stage']}): {comment['text']}")
    else:
        st.write("No comments were written.")
    answered = [row for row in summary["sensitivity"] if row["answer"]]
    if answered:
        st.markdown("**Optional sensitivity check**")
        st.dataframe([{"Scenario": items[row["scenario_id"]]["short"], "Sensitivity range": row["answer"], "Comment": row["comment"]} for row in answered], hide_index=True, width="stretch")
    if written["written"]:
        st.caption("The technical session summary was created automatically. The counts above are your own judgments, tabulated; they are not a score and not a clinical validation.")
    else:
        st.error("The technical session summary could not be written. Tell the person who runs this environment.")
    if summary["technical_problems"]:
        st.warning("A technical check found something the person who runs this environment should look at. The scenarios it concerns are not counted above.")
        LOG.warning("tone review summary technical problems: %s", "; ".join(summary["technical_problems"]))


# -- the optional sensitivity check -------------------------------------------------------------------------------------------------------------------------------
def sensitivity_chart(entry: dict, marker: int | None):
    """The three settings of the response on the SAME axes (mean arterial pressure; the table below carries the three pressures of each). Dash and marker follow the setting, never the colour alone."""
    import altair as alt
    data = [{"minute": point["minute"], "mmHg": point["map"], "setting": name} for name in ftm.SENSITIVITY_NAMES for point in entry["witnesses"][name]]
    x_max = max(point["minute"] for point in entry["witnesses"]["CENTER"]) * 1.04
    x = alt.X("minute:Q", title="Minutes", scale=alt.Scale(domain=[0, x_max], nice=False), axis=alt.Axis(tickCount=7, format="d"))
    y = alt.Y("mmHg:Q", title="MAP (mmHg)", scale=alt.Scale(domain=entry["map_range"], zero=False))
    names = list(ftm.SENSITIVITY_NAMES)
    encodings = dict(x=x, y=y, strokeDash=alt.StrokeDash("setting:N", scale=alt.Scale(domain=names, range=[SERIES[name]["dash"] for name in names]), legend=alt.Legend(title=None, orient="top")),
                     tooltip=[alt.Tooltip("setting:N", title="Setting"), alt.Tooltip("minute:Q", title="Minute"), alt.Tooltip("mmHg:Q", title="MAP (mmHg)")])
    base = alt.Chart(alt.Data(values=data))
    layers = [base.mark_line(strokeWidth=2, color=MAP_COLOR).encode(**encodings),
              base.mark_point(filled=True, size=40, color=MAP_COLOR).encode(x=x, y=y, shape=alt.Shape("setting:N", scale=alt.Scale(domain=names, range=[SERIES[name]["shape"] for name in names]), legend=None),
                                                                              tooltip=encodings["tooltip"])]
    if marker is not None:
        guide = alt.Chart(alt.Data(values=[{"minute": marker, "label": "▼ order"}]))
        layers += [guide.mark_rule(strokeDash=[2, 3], color="#8a8a8a", strokeWidth=1).encode(x="minute:Q"),
                   guide.mark_text(baseline="top", align="left", dx=4, dy=2, color="#8a8a8a", fontSize=12).encode(x="minute:Q", y=alt.value(2), text="label:N")]
    return alt.layer(*layers).properties(height=280)


def _sensitivity_table(st: Any, entry: dict) -> None:
    shown = set(entry["table_minutes"])
    rows = []
    for index, point in enumerate(entry["witnesses"]["CENTER"]):
        if point["minute"] in shown:
            rows.append({"Minute": point["minute"], **{name: f"{int(entry['witnesses'][name][index]['sbp'])}/{int(entry['witnesses'][name][index]['dbp'])} ({int(entry['witnesses'][name][index]['map'])})"
                                                      for name in ftm.SENSITIVITY_NAMES}})
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("SBP/DBP (MAP) in mmHg at the minutes listed; the graph shows every minute.")


def _sensitivity(st: Any, root: Any, reviewer: str, loaded: dict, order: list, prog: dict, bundles: Any, account: dict) -> None:
    try:
        entries = ftm.sensitivity_view(loaded["sensitivity"], loaded["items"], prog)
    except ftr.Locked:                                                           # defence in depth: the page only gets here when every scenario is submitted
        st.error("This check opens when all the scenarios are submitted.")
        return
    st.subheader("Sensitivity range check · optional")
    st.info(OPTIONAL_NOTE)
    if not entries:
        st.write("The other settings do not materially change the picture in any scenario, so there is nothing to check.")
        return
    log = ftm.SensitivityLog(root, reviewer, [entry["scenario_id"] for entry in entries], set_digest=loaded["digest"], bundles=bundles, account=account)
    state = log.state()
    flash = st.session_state.pop(tui.FLASH_KEY, None)
    if flash:
        st.error("Not saved: " + str(flash))
    if state["status"] == "UNREADABLE":
        st.error("The saved sensitivity answers cannot be read, so nothing more is recorded here. Tell the person who runs this environment.")
        LOG.warning("unreadable tone sensitivity log")
        return
    st.caption(f"{len([entry for entry in entries if entry['scenario_id'] in state['answers']])} of {len(entries)} answered · autosaved · skipping this section changes nothing")
    items = loaded["items"]
    for entry in entries:
        sid = entry["scenario_id"]
        item = items[sid]
        st.markdown(f"### {item['short']}")
        if entry["kind"] == ftm.KIND_PROBE:
            st.caption(f"{ftm.PROBE_BANNER} · {ftm.PROBE_NOTE}")
        order_minute = next((row["minute"] for row in item["timeline"] if row["intervention"]), None)
        st.altair_chart(sensitivity_chart(entry, order_minute), width="stretch")
        _sensitivity_table(st, entry)
        key = f"tn_sens_{sid}"
        tui._choice(st, key, ftm.SENSITIVITY_QUESTION, list(ftm.SENSITIVITY_CHOICES), state["answers"].get(sid), _on_envelope, (st, log, sid, key))
        note_key = f"tn_sens_{sid}_note"
        note = st.text_area("Optional comment", value=state["comments"].get(sid, ""), key=note_key, max_chars=ftr.MAX_COMMENT, on_change=_on_note, args=(st, log, sid, note_key))
        tui._unsaved_comment(st, note_key, note, state["comments"].get(sid, ""))


# -- entry ------------------------------------------------------------------------------------------------------------------------------------------------------------
def draw(st: Any, layer: Any, context: Any) -> None:
    """The whole review: header, navigation and the scenario (or the summary, or the optional check). Faculty/administrator accounts only; the page that calls it has already passed the review gate."""
    review, bundles = layer.review, layer.bundles
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        st.error(GENERIC_REFUSAL)
        return
    root = review.review_root()
    if root is None:
        st.error("The review cannot run: no review store is configured.")
        return
    loaded = ftm.load_set()
    if not loaded["ok"]:
        st.error("The stored trajectories cannot be verified, so no review can start. Tell the person who runs this environment.")
        LOG.warning("tone review set refused: %s", "; ".join(loaded["problems"]))
        return
    items, digest, audit = loaded["items"], loaded["digest"], loaded["audit"]
    reviewer = ftr.reviewer_ref(user["id"])
    order = ftm.sequence(items)
    account = {"role": user.get("role")}
    logs = {entry["scenario_id"]: ftm.ToneReviewLog(root, reviewer, items[entry["scenario_id"]], set_digest=digest, audit=audit, bundles=bundles, account=account) for entry in order}
    prog = ftm.progress(logs, order)
    summary = _verified_summary(root, reviewer, loaded, bundles) if prog["required_done"] else None
    verified = bool(summary and summary["complete"])                           # the optional check and the limitations wait for VERIFIED records, not for log statuses alone
    optional = verified and any(entry["material"] for entry in loaded["sensitivity"])
    st.header("Faculty Trajectory Review")
    st.caption("Norepinephrine and vascular tone · five scenarios · one order each")
    view = st.session_state.get(VIEW_KEY)
    if not isinstance(view, str):
        view = None
    if (view == SUMMARY_VIEW and prog["required_done"]) or (view == SENSITIVITY_VIEW and optional):
        pass
    elif view not in prog["enterable"]:
        view = SUMMARY_VIEW if (prog["required_done"] and (prog["all_done"] or view is None)) else prog["current"]
    if view is None:
        view = SUMMARY_VIEW
    _navigation(st, items, order, prog, view, optional)
    if view == SUMMARY_VIEW:
        _summary(st, root, summary or _verified_summary(root, reviewer, loaded, bundles), loaded, order)
        return
    if view == SENSITIVITY_VIEW:
        _sensitivity(st, root, reviewer, loaded, order, {**prog, "required_done": verified}, bundles, account)
        return
    _header(st, prog, order, view)
    _scenario(st, items[view], logs[view], last=prog["remaining_required"] <= 1)
