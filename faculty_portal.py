"""Faculty-only AI briefing and explicit, editable assessment drafts."""
from __future__ import annotations

import os

import streamlit as st

from account_store import AccountError
from faculty_analysis import FacultyAnalysisError, generate_faculty_brief, source_fingerprint
from faculty_analysis_store import FacultyBriefStore
from faculty_report import render_faculty_brief_pdf
from objectives import OBJECTIVES, evidence_items


ASSISTANCE = {
    "unknown": "Not known / not documented",
    "guided": "Guided - structured help directed the reasoning",
    "prompted": "Prompted - additional prompts were needed",
    "independent": "Independent - faculty has verified no additional help",
}
RECOMMENDATIONS = {
    "satisfactory": "Suggested satisfactory demonstration",
    "needs_improvement": "Suggested needs improvement",
    "insufficient_evidence": "Insufficient evidence - faculty judgment needed",
}


def _secret(name, default=""):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.environ.get(name, default) or "").strip()


def _staff_record(context, record):
    """Do not authorize private report reads from stale UI role information."""
    user = context["store"].get_user(context["token"])
    if not user or user["role"] not in {"faculty", "admin"}:
        raise AccountError("Faculty analysis is available only to faculty and administrators.")
    fresh = context["store"].get_attempt(context["token"], record["id"])
    if (not fresh or fresh["user_id"] == user["id"] or fresh["is_sandbox"]
            or fresh["status"] != "completed"
            or (fresh.get("payload", {}).get("session", {}).get("review_completed") is not True)):
        raise AccountError("Select a completed resident encounter with a completed reflection.")
    return fresh


def _assistance_key(record):
    return "faculty_assistance_" + record["id"]


def _current_report(context, record):
    assistance = st.session_state.get(_assistance_key(record))
    return FacultyBriefStore(context["store"]).get_latest(
        context["token"], record["id"], assistance_context=assistance,
    )


def _reference_text(refs, labels):
    return "; ".join(labels.get(ref, ref) + " (" + ref + ")" for ref in refs)


def render_faculty_analysis(context, record):
    if not context or context["user"]["role"] not in {"faculty", "admin"}:
        return
    session = (record.get("payload") or {}).get("session") or {}
    if record.get("status") != "completed" or session.get("review_completed") is not True:
        return
    try:
        record = _staff_record(context, record)
        brief_store = FacultyBriefStore(context["store"])
        latest = brief_store.get_latest(context["token"], record["id"])
        assistance_key = _assistance_key(record)
        if assistance_key not in st.session_state:
            st.session_state[assistance_key] = latest["assistance_context"] if latest else "unknown"
        with st.expander("AI faculty assessment brief", expanded=True):
            st.caption("Private decision support for faculty. Review suggestions against the recorded evidence before making an assessment.")
            assistance = st.selectbox("Assistance received during this encounter", list(ASSISTANCE),
                                      format_func=ASSISTANCE.get, key=assistance_key)
            st.caption("Select what you know about help received. The wording of an entry alone cannot establish independence.")
            report = latest if latest and latest["assistance_context"] == assistance else brief_store.get_latest(
                context["token"], record["id"], assistance)
            api_key = _secret("OPENAI_API_KEY")
            if not api_key:
                st.info("AI generation is unavailable until OPENAI_API_KEY is configured in the private deployment secrets. Saved reports remain available.")
            label = "Generate a new AI faculty brief" if report else "Generate AI faculty brief"
            if st.button(label, key="generate_faculty_" + record["id"], disabled=not bool(api_key)):
                record = _staff_record(context, record)
                model = _secret("MRS_FACULTY_MODEL", _secret("OPENAI_MODEL", "gpt-5.6-luna"))
                with st.spinner("Analyzing the completed encounter and its recorded evidence..."):
                    generated = generate_faculty_brief(record, api_key=api_key, model=model,
                                                       assistance_context=assistance)
                    report = brief_store.save(context["token"], record["id"], generated)
                st.success("Faculty analysis saved. Review it here or download the PDF.")
            if not report:
                st.caption("Generate a brief to review the reasoning, key decisions, evidence by objective, and suggested feedback.")
                return
            st.caption("Generated " + report["generated_at"] + " · " + report["model"])
            analysis = report["analysis"]
            st.write(analysis["summary"])
            labels = {item["ref"]: item["label"] for item in evidence_items(record["payload"])}
            st.dataframe([
                {"Objective": key["objective_id"] + " · " + OBJECTIVES[key["objective_id"]]["title"],
                 "AI suggestion": RECOMMENDATIONS[key["recommendation"]],
                 "Depth": (key["depth"] or "Faculty judgment needed").capitalize(),
                 "Autonomy": (key["autonomy"] or "Not established").capitalize()}
                for key in analysis["objectives"]
            ], hide_index=True, use_container_width=True)
            with st.expander("Read the analysis and debriefing questions"):
                for title, values in (("Strengths", analysis["strengths"]),
                                      ("Points to review", analysis["review_points"])):
                    st.markdown("**" + title + "**")
                    for value in values:
                        st.write(value)
                for decision in analysis["key_decisions"]:
                    st.caption(_reference_text(decision["evidence_refs"], labels))
                    st.write(decision["analysis"])
                    st.write("Discuss: " + decision["question"])
                st.markdown("**Reflection and adaptation**")
                st.write(analysis["learning_cycle"])
                st.markdown("**Limits of this analysis**")
                for value in analysis["limits"]:
                    st.write(value)
                for suggestion in analysis["objectives"]:
                    st.markdown("**" + suggestion["objective_id"] + " · " + OBJECTIVES[suggestion["objective_id"]]["title"] + "**")
                    st.write(suggestion["rationale"])
                    st.caption(_reference_text(suggestion["evidence_refs"], labels))
                    st.write(suggestion["feedback"])
                    for question in suggestion["questions"]:
                        st.write("Discuss: " + question)
            # A per-session byte cache avoids rerendering the same immutable PDF.
            # Authorization and source binding above are checked on every rerun.
            pdf_key = "faculty_pdf_" + report["brief_id"]
            if pdf_key not in st.session_state:
                st.session_state[pdf_key] = render_faculty_brief_pdf(report, record)
            st.download_button("Download AI faculty brief (PDF)", st.session_state[pdf_key],
                               file_name="faculty_assessment_" + record["id"][:12] + ".pdf",
                               mime="application/pdf", key="download_faculty_" + record["id"])
            st.caption("Select an objective below to load its suggestion as an editable draft. Only Record objective assessment saves your final judgment.")
    except (AccountError, FacultyAnalysisError) as exc:
        st.error(str(exc))


def render_suggestion_loader(context, record, objective_id, widget_prefix):
    """Called before form widgets are instantiated, so loading never auto-submits."""
    record = _staff_record(context, record)
    marker_key = widget_prefix + "_ai_draft"
    field_names = ("decision", "depth", "autonomy", "context", "evidence", "notes", "ack")
    marker = st.session_state.get(marker_key)
    selected_assistance = st.session_state.get(_assistance_key(record))
    if marker and (marker.get("source_hash") != source_fingerprint(record)
                   or selected_assistance is not None and marker.get("assistance_context") != selected_assistance):
        for field in field_names:
            st.session_state.pop(widget_prefix + "_" + field, None)
        st.session_state.pop(marker_key, None)
        marker = None
    try:
        report = _current_report(context, record)
    except AccountError as exc:
        # A report-storage failure must not relabel populated AI fields as a
        # manual assessment or bypass their acknowledgement/provenance.
        st.warning(str(exc))
        report = None
    if report:
        suggestion = next(item for item in report["analysis"]["objectives"] if item["objective_id"] == objective_id)
        st.caption("AI draft: " + RECOMMENDATIONS[suggestion["recommendation"]])
        st.write(suggestion["rationale"])
        if st.button("Load AI suggestion into editable form", key=widget_prefix + "_load_ai"):
            values = {
                "decision": {"satisfactory": "Satisfactory", "needs_improvement": "Needs improvement"}.get(suggestion["recommendation"]),
                "depth": suggestion["depth"], "autonomy": suggestion["autonomy"],
                "context": suggestion["context"], "evidence": list(suggestion["evidence_refs"]),
                "notes": suggestion["feedback"], "ack": False,
            }
            for field, value in values.items():
                st.session_state[widget_prefix + "_" + field] = value
            marker = {"brief_id": report["brief_id"], "source_hash": report["source_hash"],
                      "assistance_context": report["assistance_context"]}
            st.session_state[marker_key] = marker
    if marker:
        st.info("AI draft loaded. Edit every field as needed and confirm your assessment before saving. An unanswered field is not an unsatisfactory judgment.")
        if st.button("Discard loaded AI draft", key=widget_prefix + "_discard_ai"):
            for field in field_names:
                st.session_state.pop(widget_prefix + "_" + field, None)
            st.session_state.pop(marker_key, None)
            marker = None
    return marker
