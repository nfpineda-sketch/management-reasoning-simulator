"""Learner-facing synthesis of frozen evidence after independent reflection."""
from __future__ import annotations

import hashlib
import json

import streamlit as st

from account_store import AccountError
from management_trace_analysis import (
    ManagementTraceAnalysisError, build_analysis_source,
    generate_management_trace_analysis, source_fingerprint,
    validate_management_trace_analysis,
)
from management_trace_store import ManagementTraceStore


def _time(value):
    return f"{float(value):g} min"


def _reference_labels(source):
    labels = {}
    for row in source["timeline"]:
        name = f"Decision {row['decision_number']}" if row["decision_number"] else "Recorded order"
        labels[row["source_ref"]] = name + " · " + _time(row["decision_time_min"])
    for row in source["reflections"]:
        labels[row["source_ref"]] = "Later reflection on " + labels.get(row["decision_ref"], "a recorded decision")
    for row in source.get("encounter_events", []):
        labels[row["source_ref"]] = str(row.get("kind", "Encounter information")).replace("_", " ").capitalize() + " · " + _time(row.get("time_min", 0))
    return labels


def _claim(claim, labels):
    st.write(claim["text"])
    st.caption("Evidence: " + "; ".join(labels.get(ref, ref) for ref in claim["evidence_refs"]))


def _trends(source):
    import pandas as pd
    points = []
    for row in source["timeline"]:
        for field, time_field in (("state_before", "decision_time_min"), ("state_after", "response_time_min")):
            values = row[field].get("observable", {})
            point = {"Minute": row[time_field]}
            for key, label in (("hr", "HR"), ("sbp", "SBP"), ("dbp", "DBP"), ("spo2", "SpO₂")):
                value = values.get(key)
                if type(value) in (int, float):
                    point[label] = value
            points.append(point)
    if len(points) < 2:
        return
    frame = pd.DataFrame(points)
    if frame["Minute"].nunique() < 2:
        return
    for column, title, values in zip(st.columns(3), ("Heart rate · /min", "Blood pressure · mmHg", "Oxygen saturation · %"),
                                     (("HR",), ("SBP", "DBP"), ("SpO₂",))):
        selected = [key for key in values if key in frame]
        with column:
            st.caption(title)
            if selected:
                st.line_chart(frame, x="Minute", y=selected, height=175)
    st.caption("Values recorded at decision and response times. Lines connect observations; they do not represent continuous measurements.")


def render_management_trace_analysis(payload, *, api_key="", model="gpt-5-mini", context=None,
                                     case_label="", review_completed=False, adaptation_plan=None):
    """Reuse a source-bound analysis; automatic first attempt, explicit retries.

    Caller persists the locked reflection before entering this function. The
    private faculty store is never accessed here. Account analyses are stored
    separately so finalized encounter evidence stays immutable.
    """
    if payload.get("encounter_ended") is not True or payload.get("reflection_locked") is not True:
        return None
    st.subheader("Your Management Trace")
    try:
        source = build_analysis_source(payload)
        fingerprint = source_fingerprint(payload)
    except ManagementTraceAnalysisError as exc:
        st.info(str(exc))
        return None
    identity = str(context["user"]["id"]) if context else "shared-session"
    cache_key = "_learner_trace_" + identity + "_" + fingerprint
    store = None
    report = None
    try:
        if context and st.session_state.get("_attempt_id"):
            store = ManagementTraceStore(context["store"])
            # Always recheck the current account and record, including cache hits.
            report = store.get_latest(context["token"], st.session_state["_attempt_id"])
            if report is not None:
                report = validate_management_trace_analysis(report, payload)
        if report is None and store is None and cache_key in st.session_state:
            report = validate_management_trace_analysis(st.session_state[cache_key], payload)
    except (AccountError, ManagementTraceAnalysisError) as exc:
        st.error(str(exc))
        return None
    attempted = cache_key + "_attempted"
    retry = False
    if report is None and st.session_state.get(attempted):
        st.info("Your analysis was not available. The complete encounter record remains available below.")
        retry = st.button("Retry Management Trace analysis", key=cache_key + "_retry")
    if report is None and not api_key:
        st.info("AI analysis is not configured for this application. You can still review and download your original encounter record.")
        return None
    if report is None and (retry or not st.session_state.get(attempted)):
        st.session_state[attempted] = True
        try:
            with st.spinner("Connecting your decisions, expectations and observed patient responses..."):
                report = generate_management_trace_analysis(payload, api_key=api_key, model=model)
            if store:
                report = store.save(context["token"], st.session_state["_attempt_id"], report)
            st.session_state[cache_key] = report
        except (ManagementTraceAnalysisError, AccountError) as exc:
            st.error(str(exc))
            return None
    if report is None:
        return None
    st.session_state[cache_key] = report
    analysis = report["analysis"]
    labels = _reference_labels(source)
    st.caption("AI interpretation of your recorded encounter · your original decisions and locked reflection are preserved.")
    _claim(analysis["overview"], labels)
    _trends(source)
    _claim(analysis["trajectory"], labels)
    indexed = {row["source_ref"]: row for row in source["timeline"]}
    for moment in analysis["pivotal_decisions"]:
        event = indexed[moment["decision_ref"]]
        with st.container(border=True):
            st.caption(labels[moment["decision_ref"]] + " → " + _time(event["response_time_min"]))
            st.markdown("**" + moment["title"] + "**")
            left, right = st.columns(2)
            with left:
                st.markdown("**Your recorded reasoning**")
                reasoning = event["recorded_reasoning"]
                st.write(reasoning.get("problem_representation") or "A working model was not explicitly recorded.")
                if reasoning.get("management_priority"):
                    st.write("Priority: " + reasoning["management_priority"])
                st.markdown("**What you expected**")
                st.write(reasoning.get("expected_effect") or "No explicit expectation was recorded.")
            with right:
                st.markdown("**AI interpretation**")
                _claim(moment["interpretation"], labels)
                st.markdown("**Expectation and observed response**")
                _claim(moment["expected_vs_observed"], labels)
            st.markdown("**How your management evolved**")
            _claim(moment["adaptation"], labels)
            if moment["reflection_insight"]:
                with st.expander("Your later reflection"):
                    _claim(moment["reflection_insight"], labels)
            with st.expander("Recorded order and patient response"):
                st.markdown("**Order as entered**")
                st.write(event["learner_input"])
                st.markdown("**Executed actions**")
                for action in event["executed_actions"]:
                    title = action.get("label") or action.get("agent") or str(action.get("type", "Intervention")).replace("_", " ")
                    details = []
                    for field, unit in (("dose_mg", "mg"), ("dose_g", "g"), ("volume_ml", "mL"),
                                        ("flow_lpm", "L/min"), ("rate_mcg_min", "mcg/min")):
                        if field in action:
                            details.append(str(action[field]) + " " + unit)
                    if action.get("route"):
                        details.append(str(action["route"]))
                    if "time_min" in action:
                        details.append(_time(action["time_min"]))
                    st.write(str(title) + (" · " + " · ".join(details) if details else ""))
                rows = []
                before = event["state_before"].get("observable", {})
                after = event["state_after"].get("observable", {})
                for field, label in (("hr", "Heart rate"), ("sbp", "Systolic BP"), ("spo2", "SpO₂"),
                                     ("respiratory_rate", "Respiratory rate"), ("mental_status", "Mental status"),
                                     ("crt", "Capillary refill")):
                    if field in before or field in after:
                        rows.append({"Observation": label, "Before": str(before.get(field, "—")),
                                     "After": str(after.get(field, "—"))})
                st.dataframe(rows, hide_index=True, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.markdown("**Patterns to retain**")
        for claim in analysis["strengths"]:
            _claim(claim, labels)
        if not analysis["strengths"]:
            st.write("No additional evidence-supported pattern was identified.")
    with right:
        st.markdown("**Questions for your next encounter**")
        for claim in analysis["questions"]:
            _claim(claim, labels)
    from management_trace_report import RENDERER_VERSION, render_management_trace_pdf
    pdf_key = cache_key + "_pdf_" + hashlib.sha256(json.dumps(
        [report, adaptation_plan, bool(review_completed), case_label, RENDERER_VERSION],
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if pdf_key not in st.session_state:
        st.session_state[pdf_key] = render_management_trace_pdf(
            report, payload, case_label=case_label,
            review_completed=review_completed, adaptation_plan=adaptation_plan,
        )
    st.download_button("Download Management Trace PDF", st.session_state[pdf_key],
                       file_name="management_trace_v0.17.0.pdf", mime="application/pdf",
                       type="primary", key=cache_key + "_download")
    return report
