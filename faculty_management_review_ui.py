"""P3-514: the GI MANAGEMENT-TRACE REVIEW page (draws and records; decides nothing).

The same page the faculty trajectory review, the re-review, the tone review and the titration review have -- it REUSES their chart, action table, answer widgets and autosave callbacks -- for the management-trace set:
one path at a time, in this order: what you are judging, clinical context, what was done (every turn), the pressure trajectory with each intervention marked on it, the values, the MANAGEMENT TRACE (state, priority,
action, expected effect, observed response, reassessment, new state, each line with where it comes from) and the DEVELOPMENT BOUNDARY; then the five questions and Q6 (management meaning), an optional comment, ONE
button that LOCKS the first impression, the overall judgment with an optional comment, ONE submit that moves on, and a completion screen after the last.

THE SUMMARY comes after the tenth submit, never before: ``REVIEW COMPLETE · N / N``, the count of the four judgments, a table (path, overall, Q1 to Q6 and, beside Q6, the category the path was written with -- a
proposal, shown only now), the comments, and the limitations the review cannot judge, drawn only there.

REACHABLE ONLY from the faculty review launcher, for a faculty or administrator account (the page gate has already stopped everybody else); it checks the role again here. It imports nothing of the Phase-3 layer,
the engine or the common core. Nothing of the mechanism and nothing of the audit reaches the page (``fmr.load_set`` hands the audit apart), and nothing is cached in the session.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import faculty_management_review as fmr
import faculty_trajectory_review as ftr
import faculty_trajectory_review_ui as tui

LOG = logging.getLogger("faculty_management_review")
VIEW_KEY = "mt_view"
RESYNC_KEY, NOTICE_KEY = "mt_resync", "mt_notice"
SUMMARY_VIEW = "summary"
#: The operator's own switch (a process environment variable; never the Secrets file). ``off`` opens the other review modes while this review is incomplete.
OPERATOR_FLAG, OPERATOR_OPEN = "MRS_FACULTY_MANAGEMENT_GATE", "off"
GENERIC_REFUSAL = tui.GENERIC_REFUSAL
LOCK_LABEL, NEXT_LABEL, FINISH_LABEL = "LOCK FIRST IMPRESSION", "SUBMIT & NEXT", "SUBMIT & FINISH"
JUDGING_LABEL = "What you are judging"
SERIES_NAME = "Trajectory under review"
PRESSURE_ONLY_NOTE = "Heart rate, capillary refill and mental status are intentionally not displayed: only the blood pressure is produced by the development model under review."
CHART_NOTE = "Dashed vertical lines mark each intervention; the number matches the table above. The pressure is shown at each reassessment."
TRACE_NOTE = ("Each line says where it comes from: observed (what the encounter produced), model reading (a fixed reading of what the development model represents), development path (written for this "
              "scripted path and proposed for your review), resident (what a resident expressed; none here), faculty decision.")
LIMITATIONS_HEADING = "CURRENT LIMITATIONS"


def _on_overall_comment(st: Any, log: fmr.ManagementReviewLog, key: str) -> None:
    text = st.session_state.get(key) or ""
    try:
        outcome = log.overall_comment(text)
    except Exception:
        outcome = {"ok": False, "why": ftr.SAVE_FAILED}
    st.session_state[key + "__refusal"] = None if outcome["ok"] else outcome["why"]


def _header(st: Any, prog: dict, order: list, sid: str) -> None:
    position = [entry["scenario_id"] for entry in order].index(sid) + 1
    done = len(prog["submitted"])
    st.progress(min(1.0, done / max(1, len(order))))
    st.caption(f"Path {position} of {len(order)} · {done} of {len(order)} reviewed · estimated time remaining ≈ {prog['estimated_minutes_left']} min (an estimate, not a measurement)")


def _navigation(st: Any, items: dict, order: list, prog: dict, view: str) -> None:
    for start in range(0, len(order), 5):                                  # two rows of five: ten paths stay readable on one screen
        row = order[start:start + 5]
        for number, (column, entry) in enumerate(zip(st.columns(len(row)), row), start + 1):
            identifier, status = entry["scenario_id"], prog["statuses"][entry["scenario_id"]]
            allowed = status == "SUBMITTED" or identifier in prog["enterable"]
            label = ("✓ " if status == "SUBMITTED" else "") + f"{number} · {items[identifier]['short']}"
            if column.button(label, key=f"mt_nav_{identifier}", disabled=not allowed, type="primary" if identifier == view else "secondary", width="stretch"):
                st.session_state[VIEW_KEY] = identifier
                st.rerun()
    if prog["required_done"]:
        columns = st.columns([1, 4])
        if columns[0].button("Summary", key="mt_nav_summary", type="primary" if view == SUMMARY_VIEW else "secondary", width="stretch"):
            st.session_state[VIEW_KEY] = SUMMARY_VIEW
            st.rerun()


def _arrival_line(arrival: dict) -> str:
    parts = [f"BP {arrival['sbp']}/{arrival['dbp']} mmHg (MAP {arrival['map']})", f"SpO₂ {arrival['spo2']}%", f"RR {arrival['rr']}/min"]
    return "On arrival: " + " · ".join(parts) + "."


def _values_table(st: Any, item: dict) -> None:
    st.dataframe([{"Minute": row["minute"], "SBP": row["sbp"], "DBP": row["dbp"], "MAP": row["map"]} for row in fmr.values_table(item)], hide_index=True, width="stretch")
    st.caption("SBP, DBP and MAP (mmHg) at each reassessment. " + PRESSURE_ONLY_NOTE)


def _trace(st: Any, view: dict) -> None:
    """The management trace, one block per turn: each line with its label and where it comes from. The boundary block closes it."""
    st.markdown("**Management trace** · what was done, what the model represents, what was observed and what remains")
    st.caption(TRACE_NOTE)
    for block in view["trace"]:
        if block.get("boundary"):
            st.warning(f"**{block['minutes']} · {block['lines'][0]['label']}.** {block['lines'][0]['text']}"
                       + "".join(f"  \n**{line['label']}.** {line['text']}" for line in block["lines"][1:]))
            continue
        lines = [f"**{block['n']} · {block['minutes']}**"] + [f"- **{line['label']}** · _{line['tag']}_ — {line['text']}" for line in block["lines"]]
        st.markdown("\n".join(lines))


def other_modes_held(st: Any, layer: Any, context: Any) -> bool:
    """True while this reviewer has not completed this review, i.e. while the launcher must offer nothing but it. Complete means the summary counts all ten paths, which it does only for records that verify
    against the log that closed them. Whatever cannot be decided (no store, an unverifiable set, no faculty account) is HELD. The operator's switch releases it."""
    if os.environ.get(OPERATOR_FLAG, "").strip().lower() == OPERATOR_OPEN:
        return False
    review = layer.review
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        return True
    root = review.review_root()
    loaded = fmr.load_set()
    if root is None or not loaded["ok"]:
        return True
    return not _verified_summary(root, ftr.reviewer_ref(user["id"]), loaded, layer.bundles)["complete"]


def _verified_summary(root: Any, reviewer: str, loaded: dict, bundles: Any) -> dict:
    return fmr.summarize(root, reviewer, loaded["items"], fmr.sequence(loaded["items"]), loaded["digest"], loaded["audit"], loaded["limitations"], loaded["categories"], bundles=bundles)


def _lock(st: Any, log: fmr.ManagementReviewLog, sid: str, required: list, state: dict) -> None:
    """Lock the first impression ONLY if what this screen shows is what the log holds (the lock is irreversible)."""
    stale = [question for question in required if st.session_state.get(f"mt_{sid}_{question}") != state["blind"].get(question)]
    comment_key = f"mt_{sid}_comment"
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


def _case_block(st: Any, view: dict) -> None:
    st.caption(f"{view['banner']} · {view['note']}")
    st.subheader(view["title"])
    st.info(f"**{JUDGING_LABEL}.** {view['purpose']}")
    st.markdown("**Clinical context.** " + view["context"] + " " + _arrival_line(view["arrival"]))
    st.markdown("**Baseline findings (authored)**")
    st.markdown("\n".join(f"- {fact}" for fact in view["baseline_facts"]))


def _scenario(st: Any, item: dict, log: fmr.ManagementReviewLog, last: bool) -> None:
    state = log.state()
    sid = item["scenario_id"]
    if st.session_state.get(RESYNC_KEY) == sid:
        for key in [key for key in list(st.session_state.keys()) if str(key).startswith(f"mt_{sid}_")]:
            st.session_state.pop(key, None)
        st.session_state.pop(RESYNC_KEY, None)
    flash = st.session_state.pop(tui.FLASH_KEY, None)
    if flash:
        st.error("Not saved: " + str(flash))
    notice = st.session_state.pop(NOTICE_KEY, None)
    if notice:
        st.warning(str(notice))
    if state["status"] == "UNREADABLE":
        st.error("The saved answers for this path cannot be read, so nothing more is recorded for it. Tell the person who runs this environment.")
        LOG.warning("unreadable management review log for %s", sid)
        return
    view = fmr.blind_view(item)
    _case_block(st, view)
    st.markdown("**What was done** · every turn of the encounter, in order")
    tui._timeline_table(st, view, item)
    st.markdown("**Pressure trajectory** · solid lines; the dashed vertical lines mark each intervention")
    st.altair_chart(tui.pressure_chart(view["common"], None, view["markers"], None, common_name=SERIES_NAME, y_max=fmr.y_axis_max(item), x_title="Minutes since arrival"), width="stretch")
    st.caption(CHART_NOTE)
    _values_table(st, item)
    _trace(st, view)

    if not state["locked"]:
        st.markdown("**Your first impression** · saved as you go; once you lock it, it cannot be changed")
        for question in view["questions"]:
            key = f"mt_{sid}_{question['id']}"
            tui._choice(st, key, f"{question['id']} · {question['topic']}: {question['text']}", question["choices"], state["blind"].get(question["id"]), tui._on_answer, (st, log, question["id"], key))
        key = f"mt_{sid}_comment"
        comment = st.text_area("Optional comment on the path (a short note helps most when Q5 is Maybe or Yes)", value=state["blind_comment"], key=key, max_chars=ftr.MAX_COMMENT,
                               on_change=tui._on_comment, args=(st, log, key, False))
        tui._unsaved_comment(st, key, comment, state["blind_comment"])
        _, required = ftr.required_questions(item)
        ready = all(question in state["blind"] for question in required)
        if not ready:
            st.caption("Answer every question above to enable the lock.")
        if st.button(LOCK_LABEL, type="primary", disabled=not ready, key=f"mt_{sid}_lock"):
            _lock(st, log, sid, required, state)
        return

    with st.expander("Your first impression (locked)", expanded=True):
        for question in view["questions"]:
            st.write(f"{question['topic'].title()}: **{(state['locked_answers'] or {}).get(question['id'], '—')}**")
        if state["locked_comment"]:
            st.write("Comment: " + state["locked_comment"])
        st.caption(f"Locked at {state['locked_at']}")
    if state["submitted"]:
        st.success("This path is submitted. It is shown read-only.")
        st.write(f"Overall: **{state['overall']}**")
        if state["overall_comment"]:
            st.write("Overall comment: " + state["overall_comment"])
        return
    st.markdown("**Overall judgment of this path**")
    key = f"mt_{sid}_overall"
    tui._choice(st, key, "Overall judgment", list(ftr.OVERALL), state["overall"], tui._on_overall, (st, log, key))
    key = f"mt_{sid}_overall_comment"
    note = st.text_area("Optional overall comment", value=state["overall_comment"], key=key, max_chars=ftr.MAX_COMMENT, on_change=_on_overall_comment, args=(st, log, key))
    tui._unsaved_comment(st, key, note, state["overall_comment"])
    if st.button(FINISH_LABEL if last else NEXT_LABEL, type="primary", disabled=not state["overall"], key=f"mt_{sid}_submit"):
        if (st.session_state.get(key) or "") != state["overall_comment"]:
            st.error("The overall comment in the box is not saved (see the note under it). Rewrite it or clear it, then submit.")
            return
        result = log.submit()
        if result.get("ok") or result.get("record_id"):
            st.session_state[VIEW_KEY] = None
            st.rerun()
        else:
            st.error("Your review could not be saved, so nothing moved on: " + str(result.get("why") or "unknown problem") + ".")


def _summary(st: Any, root: Any, summary: dict, loaded: dict, order: list) -> None:
    items = loaded["items"]
    written = fmr.write_summary(root, summary)
    total, reviewed = len(order), len(summary["scenarios_reviewed"])
    if summary["complete"]:
        st.success(f"REVIEW COMPLETE · {reviewed} / {total}")
        st.write(fmr.COMPLETION_NOTE)
    else:
        st.warning(f"{reviewed} / {total} paths reviewed so far")
    columns = st.columns(4)
    for column, (choice, label) in zip(columns, (("ACCEPT", "Accept"), ("ACCEPT_WITH_LIMITATION", "Accept with limitation"), ("RECALIBRATE", "Recalibrate"), ("REJECT", "Reject"))):
        column.metric(label, summary["judgments"][choice])
    questions = list(ftr.FIRST_PASS) + [ftr.EXTRA_QUESTIONS[identifier] for identifier in fmr.EXTRA_QUESTIONS]
    rows = []
    for row in summary["scenarios"]:
        line = {"Path": items[row["scenario_id"]]["short"], "Overall": row["overall"], **{question["id"]: row["first_pass"].get(question["id"], "—") for question in questions}}
        if summary["complete"]:
            line["Written as (proposal)"] = row.get("proposed_category") or "—"
        rows.append(line)
    st.dataframe(rows, hide_index=True, width="stretch")
    if summary["complete"]:
        st.caption("“Written as” is the category each scripted path was written with: a proposal for your review, shown only now, beside your own Q6 answer.")
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
        st.warning("A technical check found something the person who runs this environment should look at. The paths it concerns are not counted above.")
        LOG.warning("management review summary technical problems: %s", "; ".join(summary["technical_problems"]))


def draw(st: Any, layer: Any, context: Any) -> None:
    """The whole review: header, navigation and the path (or the summary). Faculty/administrator accounts only; the page that calls it has already passed the review gate."""
    review, bundles = layer.review, layer.bundles
    user = dict(dict(context or {}).get("user") or {})
    if user.get("role") not in review.FACULTY_ROLES or user.get("id") is None:
        st.error(GENERIC_REFUSAL)
        return
    root = review.review_root()
    if root is None:
        st.error("The review cannot run: no review store is configured.")
        return
    loaded = fmr.load_set()
    if not loaded["ok"]:
        st.error("The stored paths cannot be verified, so no review can start. Tell the person who runs this environment.")
        LOG.warning("management review set refused: %s", "; ".join(loaded["problems"]))
        return
    items, digest, audit = loaded["items"], loaded["digest"], loaded["audit"]
    reviewer = ftr.reviewer_ref(user["id"])
    order = fmr.sequence(items)
    account = {"role": user.get("role")}
    logs = {entry["scenario_id"]: fmr.ManagementReviewLog(root, reviewer, items[entry["scenario_id"]], set_digest=digest, audit=audit, bundles=bundles, account=account) for entry in order}
    prog = fmr.progress(logs, order)
    summary = _verified_summary(root, reviewer, loaded, bundles) if prog["required_done"] else None
    st.header("Faculty Trajectory Review")
    st.caption("Management paths · ten paths · one hemorrhage case · each with its management trace and its development boundary")
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
