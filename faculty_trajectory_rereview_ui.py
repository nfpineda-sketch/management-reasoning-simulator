"""P3-352 to P3-355: the FACULTY TRAJECTORY RE-REVIEW page (draws and records; decides nothing).

The same page the first faculty trajectory review has -- it REUSES that page's chart, intervention table, answer widgets and autosave callbacks -- for the blind re-review set: one scenario at a time, in this
order: what you are judging, clinical context, interventions, trajectory, five questions, an optional comment, ONE button that LOCKS the first impression, the overall judgment with an optional comment, ONE submit
that moves on to the next scenario, and a completion screen after the fourth. No comparator exists here (FD-REREVIEW-05): there is no reveal button, no legacy number, no earlier trajectory and no other set.

REACHABLE ONLY from the faculty review launcher, i.e. inside a process that named the review mode and for a faculty or administrator account (the page gate has already stopped everybody else); it checks the role
again here. It imports nothing of the Phase-3 layer, the engine or the common core. The page shows clinical content only: the identity of the configuration, the audit metadata and the sources never reach
it (``rr.load_set`` hands the audit apart, and only the record writer uses it), and nothing is cached in the session.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import faculty_trajectory_review as ftr
import faculty_trajectory_review_ui as tui
import faculty_trajectory_rereview as rr

LOG = logging.getLogger("faculty_trajectory_rereview")       # what only the person who runs the environment needs: the technical reasons never reach the reviewer's screen
VIEW_KEY = "rr_view"          # its own session keys and widget keys: the first review's page and this one never share state
RESYNC_KEY, NOTICE_KEY = "rr_resync", "rr_notice"
#: The operator's own switch (a process environment variable, like the other review flags; never the Secrets file). ``off`` opens the earlier review modes while the re-review is incomplete, for the operator who needs
#: them (and for the tests of those modes). Left out, the hold of FD-REREVIEW-21 applies.
OPERATOR_FLAG, OPERATOR_OPEN = "MRS_FACULTY_REREVIEW_GATE", "off"
PRESSURE_ONLY_NOTE = ("Heart rate and capillary refill are intentionally not displayed in this blinded pressure-trajectory re-review: they were not recomputed for this trajectory.")
SUMMARY_VIEW = "summary"
GENERIC_REFUSAL = tui.GENERIC_REFUSAL
LOCK_LABEL, NEXT_LABEL, FINISH_LABEL = "LOCK FIRST IMPRESSION", "SUBMIT & NEXT", "SUBMIT & FINISH"
JUDGING_LABEL = "What you are judging"
SERIES_NAME = "Trajectory under review"       # the series name the chart tooltip shows: neutral (no authority and no comparator stand behind this review's trajectory)


def _on_overall_comment(st: Any, log: rr.ReReviewLog, key: str) -> None:
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
    st.caption(f"Re-review · scenario {position} of {len(order)} · {done} of {len(order)} reviewed · estimated time remaining ≈ {prog['estimated_minutes_left']} min (an estimate, not a measurement)")


def _navigation(st: Any, order: list, prog: dict, view: str) -> None:
    columns = st.columns(len(order) + (1 if prog["required_done"] else 0))
    for column, entry in zip(columns, order):
        identifier, status = entry["scenario_id"], prog["statuses"][entry["scenario_id"]]
        allowed = status == "SUBMITTED" or identifier in prog["enterable"]
        if column.button(("✓ " if status == "SUBMITTED" else "") + identifier, key=f"rr_nav_{identifier}", disabled=not allowed, type="primary" if identifier == view else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = identifier
            st.rerun()
    if prog["required_done"]:
        if columns[-1].button("Summary", key="rr_nav_summary", type="primary" if view == SUMMARY_VIEW else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = SUMMARY_VIEW
            st.rerun()


def _arrival_line(arrival: dict) -> str:
    """The arrival as the reviewer is shown it: pressure, oxygen saturation and respiratory rate. No heart rate and no capillary refill (FD-REREVIEW-23)."""
    parts = [f"BP {arrival['sbp']}/{arrival['dbp']} mmHg", f"SpO₂ {arrival['spo2']}%", f"RR {arrival['rr']}/min"]
    return "On arrival: " + " · ".join(part for part in parts if "None" not in part) + "."


def _values_table(st: Any, item: dict) -> None:
    st.dataframe([{"Minute": row["minute"], "SBP": row["sbp"], "DBP": row["dbp"], "MAP": row["map"]} for row in rr.values_table(item)], hide_index=True, width="stretch")
    st.caption("SBP, DBP and MAP (mmHg) are the trajectory you are judging. " + PRESSURE_ONLY_NOTE)


def prior_modes_held(st: Any, layer: Any, context: Any) -> bool:
    """FD-REREVIEW-21: True while this reviewer has not completed the re-review, i.e. while the launcher must offer nothing but the re-review. Complete means the summary counts all four scenarios, which it does only
    for records that verify against the log that closed them: a forged log does not release the hold. Whatever cannot be decided (no store, an unverifiable set, no faculty account) is HELD. The operator's
    switch (``MRS_FACULTY_REREVIEW_GATE=off``) releases it."""
    if os.environ.get(OPERATOR_FLAG, "").strip().lower() == OPERATOR_OPEN:
        return False
    review = layer.review
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        return True
    root = review.review_root()
    loaded = rr.load_set()
    if root is None or not loaded["ok"]:
        return True
    order = rr.sequence(loaded["items"])
    summary = rr.summarize(root, ftr.reviewer_ref(user["id"]), loaded["items"], order, loaded["digest"], loaded["audit"], bundles=layer.bundles)
    return not summary["complete"]


def _lock(st: Any, log: rr.ReReviewLog, sid: str, required: list, state: dict) -> None:
    """Lock the first impression ONLY if what this screen shows is what the log holds. The log is what is locked, so a screen that shows something else (another window of the same account changed an answer, or a comment
    the log refused is still in its box) must never lock behind the reviewer's back: the lock is irreversible."""
    stale = [question for question in required if st.session_state.get(f"rr_{sid}_{question}") != state["blind"].get(question)]
    comment_key = f"rr_{sid}_comment"
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
def _scenario(st: Any, item: dict, log: rr.ReReviewLog, last: bool) -> None:
    state = log.state()
    sid = item["scenario_id"]
    if st.session_state.get(RESYNC_KEY) == sid:                                  # a lock was refused because this screen showed answers the log no longer holds: the widgets are rebuilt from the log, before they are drawn
        for key in [key for key in list(st.session_state.keys()) if str(key).startswith(f"rr_{sid}_")]:
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
        LOG.warning("unreadable re-review log for %s", sid)
        return
    view = rr.blind_view(item)
    st.subheader(view["title"])
    st.info(f"**{JUDGING_LABEL}.** {view['purpose']}")
    st.markdown("**Clinical context.** " + view["context"] + " " + _arrival_line(view["arrival"]))
    st.markdown("**What was done**")
    tui._timeline_table(st, view, item)
    st.markdown("**Trajectory under review** · solid lines; numbers mark the interventions in the table")
    st.altair_chart(tui.pressure_chart(view["common"], None, tui.interventions(view["timeline"]), None, common_name=SERIES_NAME), width="stretch")
    _values_table(st, item)

    # ---- first impression: saved by callbacks as it is given, locked by ONE button
    if not state["locked"]:
        st.markdown("**Your first impression** · saved as you go; once you lock it, it cannot be changed")
        for question in view["questions"]:
            key = f"rr_{sid}_{question['id']}"
            tui._choice(st, key, f"{question['id']} · {question['topic']}: {question['text']}", question["choices"], state["blind"].get(question["id"]), tui._on_answer, (st, log, question["id"], key))
        key = f"rr_{sid}_comment"
        comment = st.text_area("Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)", value=state["blind_comment"], key=key, max_chars=ftr.MAX_COMMENT,
                               on_change=tui._on_comment, args=(st, log, key, False))
        tui._unsaved_comment(st, key, comment, state["blind_comment"])
        _, required = ftr.required_questions(item)
        ready = all(question in state["blind"] for question in required)
        if not ready:
            st.caption("Answer every question above to enable the lock.")
        if st.button(LOCK_LABEL, type="primary", disabled=not ready, key=f"rr_{sid}_lock"):
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
    key = f"rr_{sid}_overall"
    tui._choice(st, key, "Overall judgment", list(ftr.OVERALL), state["overall"], tui._on_overall, (st, log, key))
    key = f"rr_{sid}_overall_comment"
    note = st.text_area("Optional overall comment", value=state["overall_comment"], key=key, max_chars=ftr.MAX_COMMENT, on_change=_on_overall_comment, args=(st, log, key))
    tui._unsaved_comment(st, key, note, state["overall_comment"])
    if st.button(FINISH_LABEL if last else NEXT_LABEL, type="primary", disabled=not state["overall"], key=f"rr_{sid}_submit"):
        result = log.submit()
        if result.get("ok") or result.get("record_id"):
            st.session_state[VIEW_KEY] = None
            st.rerun()
        else:
            st.error("Your review could not be saved, so nothing moved on: " + str(result.get("why") or "unknown problem") + ".")


# -- completion -------------------------------------------------------------------------------------------------------------------------------------------------------
def _summary(st: Any, root: Any, reviewer: str, items: dict, order: list, digest: str, audit: dict, bundles: Any) -> None:
    summary = rr.summarize(root, reviewer, items, order, digest, audit, bundles=bundles)
    written = rr.write_summary(root, summary)
    total, reviewed = len(order), len(summary["scenarios_reviewed"])
    if summary["complete"]:
        st.success(f"RE-REVIEW COMPLETE · {reviewed} / {total}")
        st.write(rr.COMPLETION_NOTE)
    else:
        st.warning(f"{reviewed} / {total} scenarios reviewed so far")
    columns = st.columns(4)
    for column, (choice, label) in zip(columns, (("ACCEPT", "Accept"), ("ACCEPT_WITH_LIMITATION", "Accept with limitation"), ("RECALIBRATE", "Recalibrate"), ("REJECT", "Reject"))):
        column.metric(label, summary["judgments"][choice])
    st.dataframe([{"Scenario": row["scenario_id"], "Title": row["title"], "Overall": row["overall"],
                   **{question["id"]: row["first_pass"].get(question["id"], "—") for question in ftr.FIRST_PASS}} for row in summary["scenarios"]], hide_index=True, width="stretch")
    st.markdown("**Comments to follow up**")
    if summary["comments"]:
        for comment in summary["comments"]:
            st.write(f"{comment['scenario_id']} ({comment['overall']}, {comment['stage']}): {comment['text']}")
    else:
        st.write("No comments were written.")
    if written["written"]:
        st.caption("The technical session summary was created automatically. The counts above are your own judgments, tabulated; they are not a score and not a clinical validation.")
    else:
        st.error("The technical session summary could not be written. Tell the person who runs this environment.")
    if summary["technical_problems"]:
        st.warning("A technical check found something the person who runs this environment should look at. The scenarios it concerns are not counted above.")
        LOG.warning("re-review summary technical problems: %s", "; ".join(summary["technical_problems"]))


# -- entry ------------------------------------------------------------------------------------------------------------------------------------------------------------
def draw(st: Any, layer: Any, context: Any) -> None:
    """The whole re-review: header, navigation and the scenario (or the completion screen). Faculty/administrator accounts only; the page that calls it has already passed the review gate."""
    review, bundles = layer.review, layer.bundles
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        st.error(GENERIC_REFUSAL)
        return
    root = review.review_root()
    if root is None:
        st.error("The review cannot run: no review store is configured.")
        return
    loaded = rr.load_set()
    if not loaded["ok"]:
        st.error("The stored trajectories cannot be verified, so no review can start. Tell the person who runs this environment.")
        LOG.warning("re-review set refused: %s", "; ".join(loaded["problems"]))
        return
    items, digest, audit = loaded["items"], loaded["digest"], loaded["audit"]
    reviewer = ftr.reviewer_ref(user["id"])
    order = rr.sequence(items)
    account = {"role": user.get("role")}
    logs = {entry["scenario_id"]: rr.ReReviewLog(root, reviewer, items[entry["scenario_id"]], set_digest=digest, audit=audit, bundles=bundles, account=account) for entry in order}
    prog = rr.progress(logs, order)
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
        _summary(st, root, reviewer, items, order, digest, audit, bundles)
        return
    _header(st, prog, order, view)
    _scenario(st, items[view], logs[view], last=prog["remaining_required"] <= 1)
