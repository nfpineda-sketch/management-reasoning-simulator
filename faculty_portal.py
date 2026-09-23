"""Faculty-only AI briefing and explicit, editable assessment drafts."""
from __future__ import annotations

import os
from urllib.parse import urlsplit

import streamlit as st
from reportlab.platypus import LayoutError

import record_findings as findings

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
    from offline_cases import withhold
    return withhold(name, str(value or os.environ.get(name, default) or "").strip())


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


def _public_app_url():
    """Only a public origin/path may be embedded in a portable faculty PDF."""
    value = _secret("MRS_PUBLIC_APP_URL", "https://clinical-management-reasoning-ai.streamlit.app/")
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        return None
    return value


def _pdf_download(context, report, record, *, compact, assessment=None):
    # Reauthorize even when PDF bytes already exist in this Streamlit session.
    # Always render from the separately stored faculty source, never a caller's
    # learner-owned payload or a stale UI role.
    record, report = FacultyBriefStore(context["store"]).get_for_export(
        context["token"], record["id"], report["brief_id"])
    # A presentation version also invalidates byte caches for existing reports.
    app_url = _public_app_url()
    mode = "concise" if compact else "full"
    # The assessment revision is part of the key: a saved change must not be
    # served from a cached document that predates it.
    stamp = (assessment or {}).get("traceability")
    pdf_key = ("faculty_pdf_v4", context["user"]["id"], report["brief_id"], mode, app_url,
               repr(stamp) if stamp else "")
    cache_key = repr(pdf_key)
    if cache_key not in st.session_state:
        try:
            st.session_state[cache_key] = render_faculty_brief_pdf(
                report, record, compact=compact, app_url=app_url, assessment=assessment)
        except (ValueError, LayoutError):
            if compact:
                st.warning("This report could not be fitted into the concise PDF. Open the full analysis below; you can still review and record assessments.")
            else:
                st.warning("The full PDF could not be prepared. The saved analysis and assessment form remain available here.")
            return
    label = "Download 2-page faculty brief (PDF)" if compact else "Download full faculty analysis (PDF)"
    st.download_button(label, st.session_state[cache_key],
                       file_name="faculty_assessment_" + record["id"][:12] + "_" + mode + ".pdf",
                       mime="application/pdf", key="download_faculty_" + mode + "_" + record["id"])


def _training_year(context, record):
    """The year of the resident this encounter belongs to, when it is known.

    Read through the progress store, which faculty may use; ``list_users``
    is the administrator's and would answer nothing for a reviewer.
    """
    from progress_store import ProgressStore
    try:
        for person in ProgressStore(context["store"]).list_residents(context["token"]):
            if person["id"] == record.get("user_id"):
                return person.get("training_year")
    except Exception:
        return None
    return None


def _rubric_pdf_download(context, review, proposal, record):
    """The rubric assessment as its own document, for the faculty only.

    It does not depend on an AI faculty brief existing: the rubric is a
    separate report of a separate thing, and a reviewer who scored the five
    domains can print that decision without generating anything else.
    """
    from rubric_report import RubricReportError, render_rubric_report_pdf
    import rubric_progress
    from rubric_store import RubricStore
    try:
        others = [row for row in RubricStore(context["store"]).progress(
            context["token"], record.get("user_id")) if row.get("attempt_id") != record["id"]]
    except AccountError:
        others = []
    summary = rubric_progress.aggregate(others)
    average = rubric_progress.average_series(summary)
    if average:
        average = {**average, "caption": rubric_progress.caption(summary)}
    # The revision and the status are part of the key: a document served from a
    # cache that predates a saved change would show a score nobody confirmed.
    # The face, the initials and the year, for a reviewer working at a
    # distance. Absent when the resident has not agreed to store one.
    import resident_profile
    badge = resident_profile.badge(context["store"], context["token"],
                                   record.get("user_id"), _training_year(context, record))
    cache_key = repr(("rubric_pdf_v2", context["user"]["id"], record["id"],
                      review.get("sequence"), review.get("status"),
                      (proposal or {}).get("proposal_id"), summary["encounters"],
                      bool(badge), (badge or {}).get("initials")))
    if cache_key not in st.session_state:
        try:
            st.session_state[cache_key] = render_rubric_report_pdf(
                review, proposal, record, average=average, badge=badge)
        except (RubricReportError, ValueError, LayoutError):
            st.caption("The rubric document could not be prepared. The assessment above is "
                       "unchanged and remains available.")
            return
    st.download_button(
        "Download rubric assessment (PDF)", st.session_state[cache_key],
        file_name="rubric_assessment_" + record["id"][:12] + ".pdf",
        mime="application/pdf", key="download_rubric_" + record["id"])
    st.caption("Faculty document. It is not released to the resident until you have reviewed "
               "and completed it." if review.get("status") != "confirmed" else
               "Confirmed. The resident's profile now includes this encounter.")


def render_faculty_analysis(context, record):
    if not context or context["user"]["role"] not in {"faculty", "admin"}:
        return
    session = (record.get("payload") or {}).get("session") or {}
    if record.get("status") != "completed" or session.get("review_completed") is not True:
        return
    # The rubric panel is rendered first so a decision saved in this run reaches
    # the documents offered below it, rather than a revision behind.
    from rubric_portal import render_rubric_assessment
    import rubric_presentation
    try:
        saved_review = render_rubric_assessment(context, record)
    except AccountError as error:
        st.warning(str(error))
        saved_review = None
    assessment = None
    if saved_review is not None:
        from rubric_store import RubricStore
        try:
            proposal = RubricStore(context["store"]).latest_proposal(context["token"], record["id"])
        except AccountError:
            proposal = None
        assessment = rubric_presentation.summary(saved_review, proposal)
        _rubric_pdf_download(context, saved_review, proposal, record)
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
            _pdf_download(context, report, record, compact=True, assessment=assessment)
            st.caption("Start with the 2-page brief, then review an objective below, edit its draft and record your judgment. The full analysis remains available for verification.")
            labels = {item["ref"]: item["label"] for item in evidence_items(record["payload"])}
            import report_corrections, report_presentation
            correct = report_presentation.CorrectionLog(report_corrections.for_record(record))
            # The same held state the PDFs show: a negative suggestion whose
            # basis the record cannot settle waits for the faculty's reading.
            limits = findings.encounter_limits(
                ((record.get("payload") or {}).get("session") or {}).get("management_trace") or [])
            st.dataframe([
                {"Objective": key["objective_id"] + " · " + OBJECTIVES[key["objective_id"]]["title"],
                 "AI suggestion": (findings.HELD_STATUS if findings.hold_for_review(key, limits)
                                   else RECOMMENDATIONS[key["recommendation"]]),
                 "Depth": (key["depth"] or "Faculty judgment needed").capitalize(),
                 "Autonomy": (key["autonomy"] or "Not established").capitalize()}
                for key in analysis["objectives"]
            ], hide_index=True, use_container_width=True)
            with st.expander("Read the analysis and debriefing questions"):
                _pdf_download(context, report, record, compact=False, assessment=assessment)
                st.markdown("**Performance synthesis**")
                st.write(analysis["summary"])
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
                    st.write(correct(suggestion["rationale"]))
                    st.caption(_reference_text(suggestion["evidence_refs"], labels))
                    st.write(suggestion["feedback"])
                    for question in suggestion["questions"]:
                        st.write("Discuss: " + question)
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
        limits = findings.encounter_limits(
            ((record.get("payload") or {}).get("session") or {}).get("management_trace") or [])
        held = findings.hold_for_review(suggestion, limits)
        if held:
            st.caption("AI draft: " + findings.HELD_STATUS)
            st.info("AI suggestion on record: " + RECOMMENDATIONS[suggestion["recommendation"]]
                    + ". It is held for your reading because " + held[0]
                    + ". No new rating was assigned and no recorded judgment was changed.")
        else:
            st.caption("AI draft: " + RECOMMENDATIONS[suggestion["recommendation"]])
        import report_corrections, report_presentation
        correct = report_presentation.CorrectionLog(report_corrections.for_record(record))
        st.write(correct(suggestion["rationale"]))
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
