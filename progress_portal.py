"""Faculty-reviewed longitudinal progress for simulated objective components.

The resident dashboard is read-only. Numeric quotas are program settings and
never make an automatic competence decision.
"""
from datetime import datetime, timezone

import streamlit as st

from account_store import AccountError
from competency_mapping import CONTRIBUTION_LABELS, objective_is_eligible
from objectives import (
    OBJECTIVES, DEPTH_LEVELS, AUTONOMY_LEVELS,
    DEPTH_DESCRIPTIONS, AUTONOMY_DESCRIPTIONS, evidence_items,
)
from progress_store import AUTONOMY_NOT_DETERMINED, ProgressStore, pending_fields
# Named apart: the assessment form keeps its own "encounter_context" (the clinical context field).
from encounter_context import AUTONOMY_GUIDANCE, said as _said
from faculty_portal import render_suggestion_loader
from screen_language import rows as _rows, t as _t

AUTONOMY_CHOICES = (*AUTONOMY_LEVELS, AUTONOMY_NOT_DETERMINED)


def _autonomy_label(key):
    if key == AUTONOMY_NOT_DETERMINED:
        return _t("Could not be determined")
    return _t(str(key or "").capitalize())


def _date(value):
    if value is None:
        return "—"
    return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _flash(context):
    key = "_progress_message_" + context["user"]["id"]
    message = st.session_state.pop(key, None)
    if message:
        st.success(_t(message))


def _saved(context, message):
    st.session_state["_progress_message_" + context["user"]["id"]] = message
    st.rerun()


def _objective_label(objective_id):
    return objective_id + " · " + OBJECTIVES[objective_id]["title"]


def _present_evidence(items):
    for item in items:
        st.write(item["label"])
        st.json(item["details"], expanded=False)


SYNTHETIC_RUN = "Synthetic test run"


def _history_rows(observations):
    synthetic = any(row.get("synthetic_execution") for row in observations)
    return [{
        "Observed": _date(row.get("created_at")),
        "Satisfactory": "Yes" if row.get("satisfactory") else "No",
        "Depth": str(row.get("depth", "")).capitalize(),
        "Autonomy": _autonomy_label(row.get("autonomy")),
        "Context": row.get("context", ""),
        "Assessor": row.get("assessor", ""),
        "Status": "Voided" if row.get("voided") else "Recorded",
        **({"Execution": SYNTHETIC_RUN if row.get("synthetic_execution") else "—"} if synthetic else {}),
    } for row in observations]


def _satisfactory_cell(goal):
    """The counter, and what it counts when the objective requires an autonomy."""
    cell = str(goal["count"]) + "/" + str(goal["target"])
    if goal.get("required_autonomy"):
        cell += _t(" at {level} or above ({count} satisfactory)",
                   level=_autonomy_label(goal["required_autonomy"]).lower(),
                   count=goal.get("satisfactory_count", goal["count"]))
    return cell


def _render_history(goal):
    observations = goal.get("observations", [])
    if not observations:
        return
    with st.expander(_t("Observation history · ") + _objective_label(goal["objective_id"])):
        st.dataframe(_history_rows(observations), hide_index=True)
        for observation in observations:
            st.write(_date(observation.get("created_at")) + _t(" · Faculty feedback"))
            st.write(observation.get("notes", ""))
            if observation.get("voided"):
                st.caption(_t("This observation was voided and contributes no credit."))
                st.write(observation.get("void_reason", ""))
            for item in observation.get("evidence", []):
                st.caption(item.get("label", item.get("ref", _t("Recorded evidence"))))
                st.json(item.get("details", {}), expanded=False)
        decision = goal.get("confirmation")
        if decision:
            st.write(_t("Latest faculty decision · ") + _date(decision.get("updated_at")))
            st.write(decision.get("reason", ""))
            if goal.get("confirmed") and decision.get("target_at_confirmation") is not None:
                st.caption(_t("At confirmation: ") + str(decision.get("count_at_confirmation"))
                           + "/" + str(decision["target_at_confirmation"]) + _t(" satisfactory observations."))


def _progress_table(goals):
    synthetic = sum(goal.get("synthetic_count", 0) for goal in goals)
    st.dataframe(_rows([{
        "Objective": _objective_label(goal["objective_id"]),
        "Satisfactory observations": _satisfactory_cell(goal),
        "Autonomy not determined": goal.get("autonomy_not_determined_count", 0),
        **({"From synthetic test runs": goal.get("synthetic_count", 0)} if synthetic else {}),
        "Assessed encounters": goal.get("assessed_count", 0),
        "Needs improvement": goal.get("needs_improvement_count", 0),
        "Status": _t(goal["status"].replace("_", " ").capitalize()),
        "Follow-up": _t("Review later concerns") if goal.get("review_recommended") else (
            str(goal.get("post_confirmation_count", 0)) + _t(" observations since confirmation") if goal.get("post_confirmation_count") else "—"),
        # Not "not supported by the engine": trauma encounters exist and C2 is
        # disabled for another reason (DF-4, 2026-09-27).
        "Scope": goal["scope"] if goal["supported"] else _t(
            "Not enabled: current encounters are not established as offering enough opportunities "
            "to observe this objective"),
    } for goal in goals]), hide_index=True)
    st.caption(_t("These are configurable program targets. One completed encounter may contribute to several objectives. Each objective can receive at most one active observation per encounter. Only faculty-reviewed satisfactory observations increase the counter; depth and autonomy describe that observation without multiplying it."))
    st.caption(_t("Observation continues after the target and after faculty confirmation. New strengths and concerns remain in the record; they never automatically award or revoke achievement. Faculty confirmation concerns the simulated component and does not certify a workplace EPA."))
    st.caption(_t("A satisfactory observation whose autonomy could not be determined is counted and shown apart. "
               "Where an objective requires a level of autonomy, it does not meet that level: only "
               "observations at the required level count toward that objective's target."))
    if synthetic:
        st.warning(str(synthetic) + _t(" satisfactory observation(s) come from synthetic test runs: an automated "
                   "agent on a test account. They exercise the simulator and show nothing about a "
                   "person's performance."))
    for goal in goals:
        _render_history(goal)


def render_attempt_assessment(context, record):
    """Review several objectives separately against one finalized encounter."""
    if not context or context["user"]["role"] not in {"faculty", "admin"}:
        return
    try:
        record = context["store"].get_attempt(context["token"], record["id"])
        if not record or record["is_sandbox"] or record["user_id"] == context["user"]["id"]:
            st.caption(_t("Sandbox and self-assessment encounters do not contribute to resident progress."))
            return
        session = (record.get("payload") or {}).get("session") or {}
        if record["status"] != "completed" or session.get("review_completed") is not True:
            st.caption(_t("Complete the encounter and reflection before recording an objective assessment."))
            return
        progress = ProgressStore(context["store"])
        goals = progress.get_progress(context["token"], record["user_id"])["objectives"]
        items = evidence_items(record.get("payload") or {})
        st.subheader(_t("Assess observed objectives"))
        st.caption(_t("Review each demonstrated objective separately. There is no automatic credit from a completed case, a treatment keyword, or a favorable patient outcome."))
        if not items:
            st.info(_t("This completed encounter has no eligible recorded decisions or complete reflection to assess."))
            return
        with st.expander(_t("Read the recorded evidence"), expanded=False):
            _present_evidence(items)
        eligible = []
        for goal in goals:
            if not goal["supported"] or not objective_is_eligible(goal["objective_id"], record):
                continue
            already_assessed = any(
                row.get("attempt_id") == record["id"] and not row.get("voided")
                for row in goal.get("observations", [])
            )
            if already_assessed:
                st.caption(_objective_label(goal["objective_id"]) + _t(": an assessment is already recorded for this encounter."))
            else:
                eligible.append(goal["objective_id"])
        if not eligible:
            st.info(_t("There are no additional eligible objectives to assess for this encounter."))
            return
        prefix = "objective_review_" + record["id"]
        objective_id = st.selectbox(_t("Objective observed in this encounter"), eligible,
                                    format_func=_objective_label, key=prefix + "_objective")
        objective = OBJECTIVES[objective_id]
        st.write(objective["scope"])
        st.caption(objective["limitation"])
        # Where the opportunity comes from, so the faculty can judge whether it
        # really occurred (DF-1, 2026-09-27). What the case says to look for is
        # guidance: evidence it does not list still counts.
        from observation_opportunities import resolve as _opportunity
        opportunity = _opportunity(objective_id, record)
        st.caption(_t("Observation opportunity: {note}", note=_t(opportunity["note"])))
        if opportunity.get("rationale"):
            st.caption(opportunity["rationale"])
        if opportunity.get("expected_evidence"):
            st.caption(_t("What the record might show, as guidance: {items}",
                          items="; ".join(opportunity["expected_evidence"])))
        if opportunity.get("observable_component"):
            # A YES observes one component of the EPA, never all of it (TDFC, cycle 8).
            st.caption(_t("Component this encounter can show: {component}", component=opportunity["observable_component"]))
        if opportunity.get("outside_the_encounter"):
            st.caption(_t("Outside this encounter: {outside}", outside=opportunity["outside_the_encounter"]))
        if objective.get("observable_behaviors"):
            with st.expander(_t("Competency evidence to review")):
                for behavior in objective["observable_behaviors"]:
                    st.write(behavior)
                for mapping in objective.get("competency_mapping", []):
                    label = mapping["framework"] + " · " + mapping["code"]
                    st.markdown("[" + label + "](" + mapping["source_url"] + ")" if mapping.get("source_url")
                                else label)
                    # What this link contributes and what stays outside it (DF-2).
                    if mapping.get("contribution"):
                        st.caption(_t(CONTRIBUTION_LABELS[mapping["contribution"]]) + " "
                                   + str(mapping.get("component_observed") or ""))
                        if mapping.get("limitation"):
                            st.caption(_t("Not observed: {limit}", limit=mapping["limitation"]))
        st.caption(_t("Only assess what the recorded encounter demonstrates. Unobserved actions and skills outside this scope are not credited."))
        widget_prefix = prefix + "_" + objective_id
        try:
            draft = render_suggestion_loader(context, record, objective_id, widget_prefix)
        except AccountError as exc:
            st.error(str(exc))
            return
        # A saved draft of this objective comes back into the form when no AI
        # draft is loaded over it: work in progress is not lost between visits.
        saved = progress.latest_draft(context["token"], record["id"], objective_id)
        restore_key = widget_prefix + "_restored"
        if saved and not draft and st.session_state.get(restore_key) != saved["sequence"]:
            values = saved["draft"]
            st.session_state[widget_prefix + "_decision"] = (
                None if values.get("satisfactory") is None
                else "Satisfactory" if values["satisfactory"] else "Needs improvement")
            for field, key in (("depth", "depth"), ("autonomy", "autonomy"), ("context", "context"),
                               ("evidence_refs", "evidence"), ("notes", "notes")):
                if values.get(field) is not None:
                    st.session_state[widget_prefix + "_" + key] = values[field]
            st.session_state[restore_key] = saved["sequence"]
        if saved:
            st.caption(_t('Draft {v0} saved by {v1}. Still needed to confirm: ', v0=saved['sequence'], v1=saved['author'])
                       + (", ".join(_t(item) for item in saved["pending"]) if saved["pending"] else _t("nothing")) + ".")
        with st.form(widget_prefix):
            decision = st.selectbox(_t("Faculty assessment decision"), ["Satisfactory", "Needs improvement"],
                                    index=None, key=widget_prefix + "_decision", format_func=_t,
                                    placeholder=_t("Choose your assessment after reviewing the evidence"))
            satisfactory = None if decision is None else decision == "Satisfactory"
            depth = st.selectbox(_t("Observed depth"), DEPTH_LEVELS, format_func=lambda key: _t(key.capitalize()),
                                 key=widget_prefix + "_depth", index=None,
                                 placeholder=_t("Pending"),
                                 help="\n\n".join(_t(key.capitalize()) + ": " + _t(DEPTH_DESCRIPTIONS[key]) for key in DEPTH_LEVELS))
            autonomy = st.selectbox(_t("Observed autonomy"), AUTONOMY_CHOICES, format_func=_autonomy_label,
                                    key=widget_prefix + "_autonomy", index=None,
                                    placeholder=_t("Not determined: requires your confirmation"),
                                    help="\n\n".join(_t(key.capitalize()) + ": " + _t(AUTONOMY_DESCRIPTIONS[key]) for key in AUTONOMY_LEVELS)
                                    + "\n\n" + _t("Could not be determined: the record does not let you judge it. "
                                                  "It is not a negative result and not independence.")
                                    + "\n\n" + _said(AUTONOMY_GUIDANCE))
            st.caption(_t("Depth and autonomy are local observation descriptors, not ACGME milestone levels or residency years. "
                       "Autonomy is asked for only to confirm this objective; a draft can keep it pending."))
            encounter_context = st.text_input(_t("Observed clinical context"), max_chars=500, key=widget_prefix + "_context")
            references = {item["ref"]: item["label"] for item in items}
            selected_refs = st.multiselect(_t("Evidence supporting your judgment"), list(references), format_func=references.get,
                                          key=widget_prefix + "_evidence")
            notes = st.text_area(_t("Faculty rationale and feedback"), max_chars=4000,
                                 key=widget_prefix + "_notes",
                                 help=_t("Explain the judgment using the selected evidence, including any limits or areas for improvement."))
            acknowledged = st.checkbox(_t("I reviewed the AI draft and confirmed the assessment fields"), value=False,
                                        key=widget_prefix + "_ack") if draft else True
            columns = st.columns(2)
            keep = columns[0].form_submit_button(_t("Save draft"))
            submitted = columns[1].form_submit_button(_t("Record objective assessment"))
        if keep:
            kept = progress.save_draft(context["token"], record["id"], objective_id, {
                "satisfactory": satisfactory, "depth": depth, "autonomy": autonomy,
                "context": encounter_context or None, "evidence_refs": selected_refs or None,
                "notes": notes or None, **({"ai_brief_id": draft["brief_id"]} if draft else {}),
            })
            st.session_state[widget_prefix + "_restored"] = kept["sequence"]
            _saved(context, _t("Draft saved. It counts for nothing until you record the assessment.")
                   + (_t(" Still needed: ") + ", ".join(_t(item) for item in kept["pending"]) + "." if kept["pending"] else ""))
        if submitted:
            missing = pending_fields({"satisfactory": satisfactory, "depth": depth, "autonomy": autonomy,
                                      "context": encounter_context, "evidence_refs": selected_refs,
                                      "notes": notes})
            if missing or (draft and not acknowledged):
                st.error((_t("To record this objective, complete: ") + ", ".join(_t(item) for item in missing) + "." if missing else "")
                         + (_t(" Before recording, confirm your review of the AI draft.") if draft and not acknowledged else "")
                         + _t(" You can save everything else as a draft; nothing is lost."))
                return
            result = progress.assess(context["token"], record["id"], objective_id, {
                "satisfactory": satisfactory, "depth": depth, "autonomy": autonomy,
                "context": encounter_context, "evidence_refs": selected_refs, "notes": notes,
                **({"ai_brief_id": draft["brief_id"]} if draft else {}),
            })
            messages = {
                "credited": "Satisfactory observation saved. You can review another objective from this encounter.",
                "recorded": "Assessment and feedback saved without increasing the satisfactory count.",
                "duplicate": "This encounter already has an assessment for that objective; no duplicate was added.",
            }
            _saved(context, messages[result["status"]])
    except AccountError as exc:
        st.error(str(exc))


def _render_faculty_decisions(context, progress, user_id, goals):
    supported = [goal for goal in goals if goal["supported"]]
    if not supported:
        return
    with st.expander(_t("Faculty confirmation and reopening")):
        st.caption(_t("The numeric target alone does not establish achievement. Review consistency, depth, autonomy, and variation of context before confirming the simulated component."))
        selected = st.selectbox(_t("Objective for faculty decision"), [goal["objective_id"] for goal in supported],
                                format_func=_objective_label, key="faculty_decision_objective_" + user_id)
        goal = next(goal for goal in supported if goal["objective_id"] == selected)
        st.write(_t("Satisfactory observations: ") + _satisfactory_cell(goal))
        if goal.get("autonomy_not_determined_count"):
            st.caption(str(goal["autonomy_not_determined_count"]) + _t(" of them with an autonomy that could not be "
                       "determined.") + (_t(" They do not meet the required level.") if goal.get("required_autonomy") else ""))
        if goal.get("synthetic_count"):
            st.caption(str(goal["synthetic_count"]) + _t(" of them from synthetic test runs, not a person's performance."))
        st.caption(goal["limitation"])
        if goal.get("confirmed"):
            st.info(_t("Faculty confirmation is recorded. Continued observations remain available. Review new evidence to maintain confirmation or reopen the objective; both decisions retain its history."))
            if goal.get("review_recommended"):
                st.warning(str(goal["post_confirmation_needs_improvement_count"]) + _t(" later observation(s) need improvement. Review the evidence and decide whether the existing confirmation remains appropriate."))
        elif goal["count"] < goal["target"]:
            st.info(_t("The numeric target has not been reached. Confirmation becomes available after the target is reached."))
            return
        with st.form("faculty_decision_" + user_id + "_" + selected):
            maintain = False
            if goal.get("confirmed") and goal.get("post_confirmation_count"):
                maintain = st.checkbox(_t("Maintain confirmation after reviewing the continued evidence"), value=False)
            reason = st.text_area(_t("Reason for faculty decision"), max_chars=4000)
            label = ("Record follow-up decision" if goal.get("post_confirmation_count") else "Reopen objective") if goal.get("confirmed") else "Confirm simulated-component achievement"
            submitted = st.form_submit_button(label)
        if submitted:
            if goal.get("confirmed") and not maintain:
                progress.reopen(context["token"], user_id, selected, reason)
                _saved(context, "Objective reopened. Previous observations and the count have been retained.")
            else:
                progress.confirm(context["token"], user_id, selected, reason)
                _saved(context, "Faculty confirmation saved for the simulated component.")


def _render_target_settings(context, progress):
    if context["user"]["role"] != "admin":
        return
    with st.expander(_t("Program observation targets")):
        st.caption(_t("These configurable targets were supplied by the program owner. They have not been independently verified as official EPA observation requirements. A target applies across depth levels; it is not repeated for each level."))
        goals = progress.list_targets(context["token"])
        targets = {goal["objective_id"]: goal["target"] for goal in goals}
        objective_id = st.selectbox(_t("Objective target"), list(OBJECTIVES), format_func=_objective_label,
                                    key="program_target_objective")
        with st.form("program_target_" + objective_id):
            target = st.number_input(_t("Required satisfactory observations"), min_value=1, max_value=1000,
                                     value=targets[objective_id], step=1)
            reason = st.text_area(_t("Reason for target change"), max_chars=4000)
            st.caption(_t("Targets are review thresholds. Changing them preserves every observation and the recorded faculty decision; counts may exceed targets."))
            submitted = st.form_submit_button(_t("Save program target"))
        if submitted:
            progress.set_target(context["token"], objective_id, int(target), reason)
            _saved(context, "Program target saved and added to the audit history.")


VOID_REASON_NOTICE = ("The resident reads this reason on their progress page, beside the original judgment "
                      "and the notes. Write it for them to read.")


def _render_observation_correction(context, progress, user_id, goals):
    observations = {
        row["id"]: (goal["objective_id"], row)
        for goal in goals for row in goal.get("observations", [])
        if not row.get("voided")
    }
    if not observations:
        return
    with st.expander(_t("Correct a recorded assessment")):
        st.caption(_t("Void an assessment only to correct its record. The original judgment and the reason remain in the audit history. A voided satisfactory observation no longer contributes to the count."))
        selected = st.selectbox(
            _t("Assessment to void"), list(observations), key="void_observation_" + user_id,
            format_func=lambda key: observations[key][0] + " · "
            + _date(observations[key][1]["created_at"]) + " · "
            + observations[key][1].get("assessor", "Faculty"),
        )
        st.write(observations[selected][1].get("notes", ""))
        with st.form("void_assessment_" + user_id + "_" + selected):
            # The resident reads the reason (DF-24, decided 2026-09-28: A).
            st.caption(_t(VOID_REASON_NOTICE))
            reason = st.text_area(_t("Reason for voiding assessment"), max_chars=4000)
            submitted = st.form_submit_button(_t("Void assessment"))
        if submitted:
            progress.void_observation(context["token"], selected, reason)
            _saved(context, "Assessment voided. Its history has been retained and the count updated.")


def render_progress_dashboard(context, title="Objective progress"):
    """Render resident-owned progress or faculty cohort review, without assignment controls.

    Returns the resident whose record is on screen, or ``None`` for a viewer
    looking at their own. The page composes what goes beside this; nothing in
    this module knows the rubric exists, and that separation is structural
    rather than a habit (see test_rubric_is_separate_from_challenges).
    """
    if not context:
        return None
    _flash(context)
    try:
        progress = ProgressStore(context["store"])
        user = context["user"]
        st.subheader(title)
        st.caption(_t("Faculty-reviewed evidence from simulated management. This record does not certify completion of a workplace EPA."))
        if user["role"] == "resident":
            goals = progress.get_progress(context["token"])["objectives"]
            _progress_table(goals)
            return None
        learners = progress.list_residents(context["token"])
        if learners:
            # An inactive resident keeps their record, and says so (cycle 9, §154AP).
            labels = {learner["id"]: learner["username"] + ("" if learner.get("active", True) else _t(" (inactive)"))
                      for learner in learners}
            selected_user = st.selectbox(_t("Resident progress"), list(labels), format_func=labels.get,
                                         key="progress_resident")
            goals = progress.get_progress(context["token"], selected_user)["objectives"]
            _progress_table(goals)
            _render_faculty_decisions(context, progress, selected_user, goals)
            _render_observation_correction(context, progress, selected_user, goals)
        else:
            selected_user = None
            st.info(_t("No resident accounts are available yet."))
        _render_target_settings(context, progress)
        with st.expander(_t("Progress audit history")):
            st.caption(_t("Changes to assessments, targets, and faculty decisions are retained for review."))
            audit = progress.list_audit(context["token"])
            if audit:
                st.json(audit, expanded=False)
            else:
                st.caption(_t("No progress changes have been recorded."))
        return selected_user
    except AccountError as exc:
        st.error(str(exc))
        return None
