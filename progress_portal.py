"""Faculty-reviewed longitudinal progress for simulated objective components.

The resident dashboard is read-only. Numeric quotas are program settings and
never make an automatic competence decision.
"""
from datetime import datetime, timezone

import streamlit as st

from account_store import AccountError
from objectives import (
    OBJECTIVES, DEPTH_LEVELS, AUTONOMY_LEVELS,
    DEPTH_DESCRIPTIONS, AUTONOMY_DESCRIPTIONS, evidence_items,
)
from progress_store import ProgressStore
from faculty_portal import render_suggestion_loader


def _date(value):
    if value is None:
        return "—"
    return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _flash(context):
    key = "_progress_message_" + context["user"]["id"]
    message = st.session_state.pop(key, None)
    if message:
        st.success(message)


def _saved(context, message):
    st.session_state["_progress_message_" + context["user"]["id"]] = message
    st.rerun()


def _objective_label(objective_id):
    return objective_id + " · " + OBJECTIVES[objective_id]["title"]


def _present_evidence(items):
    for item in items:
        st.write(item["label"])
        st.json(item["details"], expanded=False)


def _history_rows(observations):
    return [{
        "Observed": _date(row.get("created_at")),
        "Satisfactory": "Yes" if row.get("satisfactory") else "No",
        "Depth": str(row.get("depth", "")).capitalize(),
        "Autonomy": str(row.get("autonomy", "")).capitalize(),
        "Context": row.get("context", ""),
        "Assessor": row.get("assessor", ""),
        "Status": "Voided" if row.get("voided") else "Recorded",
    } for row in observations]


def _render_history(goal):
    observations = goal.get("observations", [])
    if not observations:
        return
    with st.expander("Observation history · " + _objective_label(goal["objective_id"])):
        st.dataframe(_history_rows(observations), hide_index=True)
        for observation in observations:
            st.write(_date(observation.get("created_at")) + " · Faculty feedback")
            st.write(observation.get("notes", ""))
            if observation.get("voided"):
                st.caption("This observation was voided and contributes no credit.")
                st.write(observation.get("void_reason", ""))
            for item in observation.get("evidence", []):
                st.caption(item.get("label", item.get("ref", "Recorded evidence")))
                st.json(item.get("details", {}), expanded=False)
        decision = goal.get("confirmation")
        if decision:
            st.write("Latest faculty decision · " + _date(decision.get("updated_at")))
            st.write(decision.get("reason", ""))
            if goal.get("confirmed") and decision.get("target_at_confirmation") is not None:
                st.caption("At confirmation: " + str(decision.get("count_at_confirmation"))
                           + "/" + str(decision["target_at_confirmation"]) + " satisfactory observations.")


def _progress_table(goals):
    st.dataframe([{
        "Objective": _objective_label(goal["objective_id"]),
        "Satisfactory observations": str(goal["count"]) + "/" + str(goal["target"]),
        "Assessed encounters": goal.get("assessed_count", 0),
        "Status": goal["status"].replace("_", " ").capitalize(),
        "Scope": goal["scope"] if goal["supported"] else "Not supported by the current encounter engine",
    } for goal in goals], hide_index=True)
    st.caption("These are configurable program targets. One completed encounter may contribute to several objectives. Each objective can receive at most one active observation per encounter. Only faculty-reviewed satisfactory observations increase the counter; depth and autonomy describe that observation without multiplying it.")
    st.caption("Reaching the numeric target stops additional credit for that objective. The full encounter record remains available. Faculty confirmation is a separate judgment about the simulated component, not certification of a workplace EPA.")
    for goal in goals:
        _render_history(goal)


def render_attempt_assessment(context, record):
    """Review several objectives separately against one finalized encounter."""
    if not context or context["user"]["role"] not in {"faculty", "admin"}:
        return
    try:
        record = context["store"].get_attempt(context["token"], record["id"])
        if not record or record["is_sandbox"] or record["user_id"] == context["user"]["id"]:
            st.caption("Sandbox and self-assessment encounters do not contribute to resident progress.")
            return
        session = (record.get("payload") or {}).get("session") or {}
        if record["status"] != "completed" or session.get("review_completed") is not True:
            st.caption("Complete the encounter and reflection before recording an objective assessment.")
            return
        progress = ProgressStore(context["store"])
        goals = progress.get_progress(context["token"], record["user_id"])["objectives"]
        items = evidence_items(record.get("payload") or {})
        st.subheader("Assess observed objectives")
        st.caption("Review each demonstrated objective separately. There is no automatic credit from a completed case, a treatment keyword, or a favorable patient outcome.")
        if not items:
            st.info("This completed encounter has no eligible recorded decisions or complete reflection to assess.")
            return
        with st.expander("Read the recorded evidence", expanded=True):
            _present_evidence(items)
        eligible = []
        for goal in goals:
            if not goal["supported"]:
                continue
            already_assessed = any(
                row.get("attempt_id") == record["id"] and not row.get("voided")
                for row in goal.get("observations", [])
            )
            if goal.get("confirmed") or goal["count"] >= goal["target"]:
                st.caption(_objective_label(goal["objective_id"]) + ": the target is closed to additional credit; this encounter's full trace is retained.")
            elif already_assessed:
                st.caption(_objective_label(goal["objective_id"]) + ": an assessment is already recorded for this encounter.")
            else:
                eligible.append(goal["objective_id"])
        if not eligible:
            st.info("There are no additional eligible objectives to assess for this encounter.")
            return
        prefix = "objective_review_" + record["id"]
        objective_id = st.selectbox("Objective observed in this encounter", eligible,
                                    format_func=_objective_label, key=prefix + "_objective")
        objective = OBJECTIVES[objective_id]
        st.write(objective["scope"])
        st.caption(objective["limitation"])
        st.caption("Only assess what the recorded encounter demonstrates. Unobserved actions and skills outside this scope are not credited.")
        widget_prefix = prefix + "_" + objective_id
        try:
            draft = render_suggestion_loader(context, record, objective_id, widget_prefix)
        except AccountError as exc:
            st.error(str(exc))
            return
        with st.form(widget_prefix):
            decision = None
            if draft:
                decision = st.selectbox("Faculty assessment decision", ["Satisfactory", "Needs improvement"],
                                        index=None, key=widget_prefix + "_decision",
                                        placeholder="Choose your assessment after reviewing the evidence")
                satisfactory = decision == "Satisfactory"
            else:
                satisfactory = st.checkbox("Satisfactory demonstration of this simulated component", value=False)
            depth = st.selectbox("Observed depth", DEPTH_LEVELS, format_func=str.capitalize,
                                 key=widget_prefix + "_depth", index=None if draft else 0,
                                 help="\n\n".join(key.capitalize() + ": " + DEPTH_DESCRIPTIONS[key] for key in DEPTH_LEVELS))
            autonomy = st.selectbox("Observed autonomy", AUTONOMY_LEVELS, format_func=str.capitalize,
                                    key=widget_prefix + "_autonomy", index=None if draft else 0,
                                    help="\n\n".join(key.capitalize() + ": " + AUTONOMY_DESCRIPTIONS[key] for key in AUTONOMY_LEVELS))
            st.caption("Depth and autonomy are local observation descriptors, not ACGME milestone levels or residency years.")
            encounter_context = st.text_input("Observed clinical context", max_chars=500, key=widget_prefix + "_context")
            references = {item["ref"]: item["label"] for item in items}
            selected_refs = st.multiselect("Evidence supporting your judgment", list(references), format_func=references.get,
                                          key=widget_prefix + "_evidence")
            notes = st.text_area("Faculty rationale and feedback", max_chars=4000,
                                 key=widget_prefix + "_notes",
                                 help="Explain the judgment using the selected evidence, including any limits or areas for improvement.")
            acknowledged = st.checkbox("I reviewed the AI draft and confirmed the assessment fields", value=False,
                                        key=widget_prefix + "_ack") if draft else True
            submitted = st.form_submit_button("Record objective assessment")
        if submitted:
            if draft and (decision is None or depth is None or autonomy is None or not acknowledged):
                st.error("Choose your assessment, depth and autonomy, and confirm your review of the AI draft before saving.")
                return
            result = progress.assess(context["token"], record["id"], objective_id, {
                "satisfactory": satisfactory, "depth": depth, "autonomy": autonomy,
                "context": encounter_context, "evidence_refs": selected_refs, "notes": notes,
                **({"ai_brief_id": draft["brief_id"]} if draft else {}),
            })
            messages = {
                "credited": "Satisfactory observation saved. You can review another objective from this encounter.",
                "recorded": "Assessment and feedback saved without increasing the satisfactory count.",
                "capped": "The objective is already closed to additional credit. The encounter record is retained.",
                "duplicate": "This encounter already has an assessment for that objective; no duplicate was added.",
            }
            _saved(context, messages[result["status"]])
    except AccountError as exc:
        st.error(str(exc))


def _render_faculty_decisions(context, progress, user_id, goals):
    supported = [goal for goal in goals if goal["supported"]]
    if not supported:
        return
    with st.expander("Faculty confirmation and reopening"):
        st.caption("The numeric target alone does not establish achievement. Review consistency, depth, autonomy, and variation of context before confirming the simulated component.")
        selected = st.selectbox("Objective for faculty decision", [goal["objective_id"] for goal in supported],
                                format_func=_objective_label, key="faculty_decision_objective_" + user_id)
        goal = next(goal for goal in supported if goal["objective_id"] == selected)
        st.write(f"Satisfactory observations: {goal['count']}/{goal['target']}")
        st.caption(goal["limitation"])
        if goal.get("confirmed"):
            st.info("Faculty confirmation is recorded. Reopening retains the observation history and current count. Collecting more credit also requires a target above that count.")
        elif goal["count"] < goal["target"]:
            st.info("The numeric target has not been reached. Confirmation becomes available after the target is reached.")
            return
        with st.form("faculty_decision_" + user_id + "_" + selected):
            reason = st.text_area("Reason for faculty decision", max_chars=4000)
            label = "Reopen objective" if goal.get("confirmed") else "Confirm simulated-component achievement"
            submitted = st.form_submit_button(label)
        if submitted:
            if goal.get("confirmed"):
                progress.reopen(context["token"], user_id, selected, reason)
                _saved(context, "Objective reopened. Previous observations and the count have been retained.")
            else:
                progress.confirm(context["token"], user_id, selected, reason)
                _saved(context, "Faculty confirmation saved for the simulated component.")


def _render_target_settings(context, progress):
    if context["user"]["role"] != "admin":
        return
    with st.expander("Program observation targets"):
        st.caption("These configurable targets were supplied by the program owner. They have not been independently verified as official EPA observation requirements. A target applies across depth levels; it is not repeated for each level.")
        goals = progress.list_targets(context["token"])
        targets = {goal["objective_id"]: goal["target"] for goal in goals}
        objective_id = st.selectbox("Objective target", list(OBJECTIVES), format_func=_objective_label,
                                    key="program_target_objective")
        with st.form("program_target_" + objective_id):
            target = st.number_input("Required satisfactory observations", min_value=1, max_value=1000,
                                     value=targets[objective_id], step=1)
            reason = st.text_area("Reason for target change", max_chars=4000)
            st.caption("Targets cannot be lowered below an existing satisfactory count. Increasing a target does not reopen a faculty-confirmed objective; reopen it separately when needed.")
            submitted = st.form_submit_button("Save program target")
        if submitted:
            progress.set_target(context["token"], objective_id, int(target), reason)
            _saved(context, "Program target saved and added to the audit history.")


def _render_observation_correction(context, progress, user_id, goals):
    observations = {
        row["id"]: (goal["objective_id"], row)
        for goal in goals for row in goal.get("observations", [])
        if not row.get("voided")
    }
    if not observations:
        return
    with st.expander("Correct a recorded assessment"):
        st.caption("Void an assessment only to correct its record. The original judgment and the reason remain in the audit history. A voided satisfactory observation no longer contributes to the count.")
        selected = st.selectbox(
            "Assessment to void", list(observations), key="void_observation_" + user_id,
            format_func=lambda key: observations[key][0] + " · "
            + _date(observations[key][1]["created_at"]) + " · "
            + observations[key][1].get("assessor", "Faculty"),
        )
        st.write(observations[selected][1].get("notes", ""))
        with st.form("void_assessment_" + user_id + "_" + selected):
            reason = st.text_area("Reason for voiding assessment", max_chars=4000)
            submitted = st.form_submit_button("Void assessment")
        if submitted:
            progress.void_observation(context["token"], selected, reason)
            _saved(context, "Assessment voided. Its history has been retained and the count updated.")


def render_progress_dashboard(context, title="Objective progress"):
    """Render resident-owned progress or faculty cohort review, without assignment controls."""
    if not context:
        return
    _flash(context)
    try:
        progress = ProgressStore(context["store"])
        user = context["user"]
        st.subheader(title)
        st.caption("Faculty-reviewed evidence from simulated management. This record does not certify completion of a workplace EPA.")
        if user["role"] == "resident":
            goals = progress.get_progress(context["token"])["objectives"]
            _progress_table(goals)
            return
        learners = progress.list_residents(context["token"])
        if learners:
            labels = {learner["id"]: learner["username"] for learner in learners}
            selected_user = st.selectbox("Resident progress", list(labels), format_func=labels.get,
                                         key="progress_resident")
            goals = progress.get_progress(context["token"], selected_user)["objectives"]
            _progress_table(goals)
            _render_faculty_decisions(context, progress, selected_user, goals)
            _render_observation_correction(context, progress, selected_user, goals)
        else:
            st.info("No resident accounts are available yet.")
        _render_target_settings(context, progress)
        with st.expander("Progress audit history"):
            st.caption("Changes to assessments, targets, and faculty decisions are retained for review.")
            audit = progress.list_audit(context["token"])
            if audit:
                st.json(audit, expanded=False)
            else:
                st.caption("No progress changes have been recorded.")
    except AccountError as exc:
        st.error(str(exc))
