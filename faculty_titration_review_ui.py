"""P3-441 to P3-443: the NOREPINEPHRINE TITRATION REVIEW page (draws and records; decides nothing).

The same page the faculty trajectory review, the re-review and the multifamily tone review have -- it REUSES their chart, intervention table, answer widgets and autosave callbacks -- for the titration set: one
scenario at a time, in this order: what you are judging, clinical context, what was done (every change of the norepinephrine rate), the pressure trajectory with each change marked on it, five questions, an optional
comment, ONE button that LOCKS the first impression, the overall judgment with an optional comment, ONE submit that moves on to the next scenario, and a completion screen after the last. No comparator exists here:
there is no reveal step, no legacy number, no earlier trajectory, no other setting of the response and no other set; no mechanism exists in a scenario's view.

THE SUMMARY comes after the fifth submit, never before: ``REVIEW COMPLETE · N / N``, the count of the four judgments, a table (scenario, overall, Q1 to Q5), the comments, and the current limitations that the review
cannot judge, drawn only there.

REACHABLE ONLY from the faculty review launcher, i.e. inside a process that named the review mode and for a faculty or administrator account (the page gate has already stopped everybody else); it checks the role
again here. It imports nothing of the Phase-3 layer, the engine or the common core. The page shows clinical content only: the audit metadata and the sources never reach it (``ftt.load_set`` hands them apart, and
only the record writer uses them), and nothing is cached in the session.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import faculty_titration_review as ftt
import faculty_trajectory_review as ftr
import faculty_trajectory_review_ui as tui

LOG = logging.getLogger("faculty_titration_review")       # what only the person who runs the environment needs: the technical reasons never reach the reviewer's screen
VIEW_KEY = "tt_view"          # its own session keys and widget keys: the other reviews' pages and this one never share state
RESYNC_KEY, NOTICE_KEY = "tt_resync", "tt_notice"
SUMMARY_VIEW = "summary"
#: The operator's own switch (a process environment variable, like the other review flags; never the Secrets file). ``off`` opens the other review modes while this review is incomplete, for the operator who needs them
#: (and for the tests of those modes). Left out, the other modes are held until this reviewer's five scenarios are submitted and verified.
OPERATOR_FLAG, OPERATOR_OPEN = "MRS_FACULTY_TITRATION_GATE", "off"
GENERIC_REFUSAL = tui.GENERIC_REFUSAL
LOCK_LABEL, NEXT_LABEL, FINISH_LABEL = "LOCK FIRST IMPRESSION", "SUBMIT & NEXT", "SUBMIT & FINISH"
JUDGING_LABEL = "What you are judging"
SERIES_NAME = "Trajectory under review"       # the series name the chart tooltip shows: neutral (no authority and no comparator stand behind this review's trajectory)
PRESSURE_ONLY_NOTE = ("Heart rate and capillary refill are intentionally not displayed in this pressure-trajectory review: they were not recomputed for these trajectories.")
CHART_NOTE = "Dashed vertical lines mark each change of the norepinephrine rate (mcg/min); the number matches the table above."
LIMITATIONS_HEADING = "CURRENT LIMITATIONS"


def _on_overall_comment(st: Any, log: ftt.TitrationReviewLog, key: str) -> None:
    text = st.session_state.get(key) or ""
    try:
        outcome = log.overall_comment(text)
    except Exception:                                                        # whatever happens, the browser never gets a traceback with a path
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    st.session_state[key + "__refusal"] = None if outcome["ok"] else outcome["why"]


def _header(st: Any, prog: dict, order: list, sid: str) -> None:
    position = [entry["scenario_id"] for entry in order].index(sid) + 1
    done = len(prog["submitted"])
    st.progress(min(1.0, done / max(1, len(order))))
    st.caption(f"Scenario {position} of {len(order)} · {done} of {len(order)} reviewed · estimated time remaining ≈ {prog['estimated_minutes_left']} min (an estimate, not a measurement)")


def _navigation(st: Any, items: dict, order: list, prog: dict, view: str) -> None:
    for number, (column, entry) in enumerate(zip(st.columns(len(order)), order), 1):
        identifier, status = entry["scenario_id"], prog["statuses"][entry["scenario_id"]]
        allowed = status == "SUBMITTED" or identifier in prog["enterable"]
        label = ("✓ " if status == "SUBMITTED" else "") + f"{number} · {items[identifier]['short']}"
        if column.button(label, key=f"tt_nav_{identifier}", disabled=not allowed, type="primary" if identifier == view else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = identifier
            st.rerun()
    if prog["required_done"]:                                           # a second, shorter row: the summary is offered only once every scenario is submitted
        columns = st.columns([1, 4])
        if columns[0].button("Summary", key="tt_nav_summary", type="primary" if view == SUMMARY_VIEW else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = SUMMARY_VIEW
            st.rerun()


def _arrival_line(arrival: dict) -> str:
    """The arrival of the case as the reviewer is shown it: pressure, oxygen saturation and respiratory rate. No heart rate and no capillary refill."""
    parts = [f"BP {arrival['sbp']}/{arrival['dbp']} mmHg (MAP {arrival['map']})", f"SpO₂ {arrival['spo2']}%", f"RR {arrival['rr']}/min"]
    return "On arrival: " + " · ".join(parts) + "."


def _values_table(st: Any, item: dict) -> None:
    st.dataframe([{"Minute": row["minute"], "SBP": row["sbp"], "DBP": row["dbp"], "MAP": row["map"]} for row in ftt.values_table(item)], hide_index=True, width="stretch")
    st.caption("SBP, DBP and MAP (mmHg) at the minutes listed are the trajectory you are judging; the graph shows every minute. " + PRESSURE_ONLY_NOTE)


def other_modes_held(st: Any, layer: Any, context: Any) -> bool:
    """True while this reviewer has not completed this review, i.e. while the launcher must offer nothing but it: the first review, the re-review, the multifamily tone review and the live encounter draw earlier
    trajectories, the legacy comparator, heart rate and capillary refill and the reviewer's earlier judgments, none of which may be reachable from a blind first pass. Complete means the summary counts all five
    scenarios, which it does only for records that verify against the log that closed them: a forged log does not release the hold. Whatever cannot be decided (no store, an unverifiable set, no faculty account) is
    HELD. The operator's switch releases it."""
    if os.environ.get(OPERATOR_FLAG, "").strip().lower() == OPERATOR_OPEN:
        return False
    review = layer.review
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        return True
    root = review.review_root()
    loaded = ftt.load_set()
    if root is None or not loaded["ok"]:
        return True
    return not _verified_summary(root, ftr.reviewer_ref(user["id"]), loaded, layer.bundles)["complete"]


def _verified_summary(root: Any, reviewer: str, loaded: dict, bundles: Any) -> dict:
    """The summary derived ONLY from records that verify against the logs that closed them: the one source of 'complete' for everything that depends on it (the limitations and the other modes)."""
    return ftt.summarize(root, reviewer, loaded["items"], ftt.sequence(loaded["items"]), loaded["digest"], loaded["audit"], loaded["limitations"], bundles=bundles)


def _lock(st: Any, log: ftt.TitrationReviewLog, sid: str, required: list, state: dict) -> None:
    """Lock the first impression ONLY if what this screen shows is what the log holds. The log is what is locked, so a screen that shows something else (another window of the same account changed an answer, or a comment
    the log refused is still in its box) must never lock behind the reviewer's back: the lock is irreversible."""
    stale = [question for question in required if st.session_state.get(f"tt_{sid}_{question}") != state["blind"].get(question)]
    comment_key = f"tt_{sid}_comment"
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
    """The clinical context of the scenario: the label, the question, the authored context and findings, and the baseline pressure. Nothing of the mechanism."""
    st.caption(f"{view['banner']} · {view['note']}")
    st.subheader(view["title"])
    st.info(f"**{JUDGING_LABEL}.** {view['purpose']}")
    st.markdown("**Clinical context.** " + view["context"] + " " + _arrival_line(view["arrival"]))
    st.markdown("**Baseline findings (authored)**")
    st.markdown("\n".join(f"- {fact}" for fact in view["baseline_facts"]))


def _scenario(st: Any, item: dict, log: ftt.TitrationReviewLog, last: bool) -> None:
    state = log.state()
    sid = item["scenario_id"]
    if st.session_state.get(RESYNC_KEY) == sid:                                  # a lock was refused because this screen showed answers the log no longer holds: the widgets are rebuilt from the log, before they are drawn
        for key in [key for key in list(st.session_state.keys()) if str(key).startswith(f"tt_{sid}_")]:
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
        LOG.warning("unreadable titration review log for %s", sid)
        return
    view = ftt.blind_view(item)
    _case_block(st, view)
    st.markdown("**What was done** · every change of the norepinephrine rate")
    tui._timeline_table(st, view, item)
    st.caption(view["intervention"])
    st.markdown("**Pressure trajectory** · solid lines; the dashed vertical lines mark the changes of the rate")
    st.altair_chart(tui.pressure_chart(view["common"], None, view["markers"], None, common_name=SERIES_NAME, y_max=ftt.y_axis_max(item), x_title="Minutes since arrival"), width="stretch")
    st.caption(CHART_NOTE)
    _values_table(st, item)

    # ---- first impression: saved by callbacks as it is given, locked by ONE button
    if not state["locked"]:
        st.markdown("**Your first impression** · saved as you go; once you lock it, it cannot be changed")
        for question in view["questions"]:
            key = f"tt_{sid}_{question['id']}"
            tui._choice(st, key, f"{question['id']} · {question['topic']}: {question['text']}", question["choices"], state["blind"].get(question["id"]), tui._on_answer, (st, log, question["id"], key))
        key = f"tt_{sid}_comment"
        comment = st.text_area("Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)", value=state["blind_comment"], key=key, max_chars=ftr.MAX_COMMENT,
                               on_change=tui._on_comment, args=(st, log, key, False))
        tui._unsaved_comment(st, key, comment, state["blind_comment"])
        _, required = ftr.required_questions(item)
        ready = all(question in state["blind"] for question in required)
        if not ready:
            st.caption("Answer every question above to enable the lock.")
        if st.button(LOCK_LABEL, type="primary", disabled=not ready, key=f"tt_{sid}_lock"):
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
    key = f"tt_{sid}_overall"
    tui._choice(st, key, "Overall judgment", list(ftr.OVERALL), state["overall"], tui._on_overall, (st, log, key))
    key = f"tt_{sid}_overall_comment"
    note = st.text_area("Optional overall comment", value=state["overall_comment"], key=key, max_chars=ftr.MAX_COMMENT, on_change=_on_overall_comment, args=(st, log, key))
    tui._unsaved_comment(st, key, note, state["overall_comment"])
    if st.button(FINISH_LABEL if last else NEXT_LABEL, type="primary", disabled=not state["overall"], key=f"tt_{sid}_submit"):
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
    written = ftt.write_summary(root, summary)
    total, reviewed = len(order), len(summary["scenarios_reviewed"])
    if summary["complete"]:
        st.success(f"REVIEW COMPLETE · {reviewed} / {total}")
        st.write(ftt.COMPLETION_NOTE)
    else:
        st.warning(f"{reviewed} / {total} scenarios reviewed so far")
    columns = st.columns(4)
    for column, (choice, label) in zip(columns, (("ACCEPT", "Accept"), ("ACCEPT_WITH_LIMITATION", "Accept with limitation"), ("RECALIBRATE", "Recalibrate"), ("REJECT", "Reject"))):
        column.metric(label, summary["judgments"][choice])
    st.dataframe([{"Scenario": items[row["scenario_id"]]["short"], "Overall": row["overall"], **{question["id"]: row["first_pass"].get(question["id"], "—") for question in ftr.FIRST_PASS}}
                  for row in summary["scenarios"]], hide_index=True, width="stretch")
    if summary["complete"]:
        st.markdown(f"**{LIMITATIONS_HEADING}**")
        st.markdown("\n".join(f"- {entry['text']}" for entry in summary["limitations"]))
    st.markdown("**Comments to follow up**")
    if summary["comments"]:
        for comment in summary["comments"]:
            st.write(f"{items[comment['scenario_id']]['short']} ({comment['overall']}, {comment['stage']}): {comment['text']}")
    else:
        st.write("No comments were written.")
    if written["written"]:
        st.caption("The technical session summary was created automatically. The counts above are your own judgments, tabulated; they are not a score and not a clinical validation.")
    else:
        st.error("The technical session summary could not be written. Tell the person who runs this environment.")
    if summary["technical_problems"]:
        st.warning("A technical check found something the person who runs this environment should look at. The scenarios it concerns are not counted above.")
        LOG.warning("titration review summary technical problems: %s", "; ".join(summary["technical_problems"]))


# -- entry ------------------------------------------------------------------------------------------------------------------------------------------------------------
def draw(st: Any, layer: Any, context: Any) -> None:
    """The whole review: header, navigation and the scenario (or the summary). Faculty/administrator accounts only; the page that calls it has already passed the review gate."""
    review, bundles = layer.review, layer.bundles
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        st.error(GENERIC_REFUSAL)
        return
    root = review.review_root()
    if root is None:
        st.error("The review cannot run: no review store is configured.")
        return
    loaded = ftt.load_set()
    if not loaded["ok"]:
        st.error("The stored trajectories cannot be verified, so no review can start. Tell the person who runs this environment.")
        LOG.warning("titration review set refused: %s", "; ".join(loaded["problems"]))
        return
    items, digest, audit = loaded["items"], loaded["digest"], loaded["audit"]
    reviewer = ftr.reviewer_ref(user["id"])
    order = ftt.sequence(items)
    account = {"role": user.get("role")}
    logs = {entry["scenario_id"]: ftt.TitrationReviewLog(root, reviewer, items[entry["scenario_id"]], set_digest=digest, audit=audit, bundles=bundles, account=account) for entry in order}
    prog = ftt.progress(logs, order)
    summary = _verified_summary(root, reviewer, loaded, bundles) if prog["required_done"] else None
    st.header("Faculty Trajectory Review")
    st.caption("Norepinephrine rate changes · five scenarios · one hemorrhage case")
    view = st.session_state.get(VIEW_KEY)
    if not isinstance(view, str):
        view = None
    if view == SUMMARY_VIEW and prog["required_done"]:
        pass
    elif view not in prog["enterable"]:
        view = SUMMARY_VIEW if (prog["required_done"] and (prog["all_done"] or view is None)) else prog["current"]
    if view is None:
        view = SUMMARY_VIEW
    _navigation(st, items, order, prog, view)
    if view == SUMMARY_VIEW:
        _summary(st, root, summary or _verified_summary(root, reviewer, loaded, bundles), loaded, order)
        return
    _header(st, prog, order, view)
    _scenario(st, items[view], logs[view], last=prog["remaining_required"] <= 1)
