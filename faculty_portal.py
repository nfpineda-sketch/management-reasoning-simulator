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


# The context a brief written before 2026-09-24 was generated under: the
# faculty chose one of the autonomy levels before the analysis. Kept to read
# those briefs; no longer offered.
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


def _current_report(context, record):
    """The latest saved brief for this encounter revision, whatever it was written under."""
    return FacultyBriefStore(context["store"]).get_latest(context["token"], record["id"])


def _when(value):
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OverflowError, OSError):
        return "time not recorded"


def _declared(row, field="assistance"):
    """One line: what was declared, by whom and when -- or that nobody declared it."""
    import encounter_context
    if row is None:
        return (encounter_context.label(field, "not_reported") + " - nobody has declared it yet"
                if field == "assistance" else "")
    text = (encounter_context.label(field, row["value"]) + " - declared by the "
            + str(row["declared_by_role"]) + " (" + str(row["declared_by"]) + "), "
            + _when(row["declared_at"]))
    if row.get("description"):
        text += ". Help described: " + row["description"]
    if row.get("note"):
        text += ". Note: " + row["note"]
    return text


def render_assistance_context(context, record):
    """The declared assistance context, its history, and the faculty's own entry.

    Faculty specification of 2026-09-24, section 8: who declared what help and
    when; the clinical help recorded, if any; and a way to complete or correct
    the declaration without overwriting anything already confirmed.
    """
    import encounter_context
    store = encounter_context.EncounterContextStore(context["store"])
    current = store.current(context["token"], record["id"])
    st.markdown("**Assistance context**")
    st.caption(_declared(current["assistance"]))
    if current["execution"] is not None:
        st.caption(_declared(current["execution"], "execution"))
    st.caption(encounter_context.NO_CLINICAL_HELP_FEATURE[0])
    history = store.history(context["token"], record["id"])
    if len(history) > 1:
        with st.expander(f"Declaration history ({len(history)})"):
            for row in history:
                st.caption(f"{row['field']} {row['sequence']}: {_declared(row, row['field'])}")
    with st.expander("Complete or correct the assistance context"):
        st.caption("A new declaration is added to the history; nothing earlier is overwritten, "
                   "and no assessment already confirmed changes.")
        decisions = {item["ref"]: item["label"] for item in evidence_items(record["payload"])
                     if item["kind"] == "decision"}
        with st.form("assistance_context_" + record["id"]):
            value = st.radio("Help received during the encounter", list(encounter_context.ASSISTANCE),
                             format_func=lambda key: encounter_context.label("assistance", key),
                             index=None, horizontal=True)
            description = st.text_area("What help, if any (optional)", max_chars=1000)
            affected = st.multiselect("Decisions the help affected (optional)", list(decisions),
                                      format_func=decisions.get)
            note = st.text_input("Why you are completing or correcting it (optional)", max_chars=1000)
            submitted = st.form_submit_button("Save declaration")
        if submitted:
            if value is None:
                st.error("Choose what is known about the help received.")
            else:
                store.declare(context["token"], record["id"], value=value,
                              description=description if value == "external_help" else "",
                              affected_refs=affected if value == "external_help" else (),
                              note=note)
                st.success("Declaration saved and added to the history.")
                current = store.current(context["token"], record["id"])
    return current


def _reference_text(refs, labels):
    # What a reader follows is the decision and its time; the stored
    # identifier stays in the record (2026-09-24).
    return "; ".join(labels.get(ref, "Reference unavailable") for ref in refs)


def _labels(record):
    """"Decision 2 · 00:04" for every citable item, from the same map the documents use."""
    import report_presentation
    session = ((record.get("payload") or {}).get("session") or {})
    resolved = report_presentation.reference_labels(session.get("management_trace") or [])
    labels = {}
    for item in evidence_items(record["payload"]):
        at = (resolved.get(item["ref"]) or {}).get("en", "")
        clock = at.split(" · ", 1)[1] if " · " in at else ""
        labels[item["ref"]] = item["label"] + (" · " + clock if clock else "")
    return labels


def _prose(record):
    """The model's words for a screen: recorded corrections, then identifiers resolved."""
    import report_corrections, report_presentation
    session = ((record.get("payload") or {}).get("session") or {})
    return report_presentation.CorrectionLog(
        report_corrections.for_record(record),
        references=report_presentation.reference_labels(session.get("management_trace") or []),
        language="en")


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
    review_key = review or {}
    cache_key = repr(("rubric_pdf_v2", context["user"]["id"], record["id"],
                      review_key.get("sequence"), review_key.get("status"),
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
               "and completed it." if review_key.get("status") != "confirmed" else
               "Confirmed. The resident's profile now includes this encounter.")


def proposal_for_document(store, token, record, saved_review):
    """The proposal a rubric document shows beside the faculty's decision.

    A decision is compared with the proposal it started from, never with one
    generated after it; a confirmed decision made without any proposal shows
    none; before a decision, the latest proposal is what is being reviewed
    (faculty decision 15, 2026-09-25).
    """
    if saved_review is not None and saved_review.get("proposal_id"):
        return store.proposal(token, record["id"], saved_review["proposal_id"])
    if saved_review is not None and saved_review.get("status") == "confirmed":
        return None
    return store.latest_proposal(token, record["id"])


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
        saved_review = render_rubric_assessment(
            context, record, training_year=_training_year(context, record))
    except AccountError as error:
        st.warning(str(error))
        saved_review = None
    assessment = None
    from rubric_store import RubricStore
    try:
        proposal = proposal_for_document(RubricStore(context["store"]), context["token"], record,
                                         saved_review)
    except AccountError:
        proposal = None
    if saved_review is not None:
        assessment = rubric_presentation.summary(saved_review, proposal, record=record)
        _rubric_pdf_download(context, saved_review, proposal, record)
    elif proposal is not None:
        # The proposal can be printed before any decision; nothing is saved.
        _rubric_pdf_download(context, None, proposal, record)
    try:
        record = _staff_record(context, record)
        brief_store = FacultyBriefStore(context["store"])
        report = brief_store.get_latest(context["token"], record["id"])
        with st.expander("AI faculty assessment brief", expanded=True):
            st.caption("Private decision support for faculty. Review suggestions against the recorded evidence before making an assessment.")
            import encounter_context
            declared = render_assistance_context(context, record)
            st.caption("An unreported context is a valid state: the brief is generated either way, "
                       "and an autonomy the record cannot establish is left for your confirmation.")
            api_key = _secret("OPENAI_API_KEY")
            if not api_key:
                st.info("AI generation is unavailable until OPENAI_API_KEY is configured in the private deployment secrets. Saved reports remain available.")
            label = "Generate a new AI faculty brief" if report else "Generate AI faculty brief"
            if st.button(label, key="generate_faculty_" + record["id"], disabled=not bool(api_key)):
                record = _staff_record(context, record)
                model = _secret("MRS_FACULTY_MODEL", _secret("OPENAI_MODEL", "gpt-5.6-luna"))
                with st.spinner("Analyzing the completed encounter and its recorded evidence..."):
                    generated = generate_faculty_brief(
                        record, api_key=api_key, model=model,
                        context=encounter_context.snapshot(declared))
                    report = brief_store.save(context["token"], record["id"], generated)
                st.success("Faculty analysis saved. Review it here or download the PDF.")
            if not report:
                st.caption("Generate a brief to review the reasoning, key decisions, evidence by objective, and suggested feedback.")
                return
            st.caption("Generated " + report["generated_at"] + " · " + report["model"])
            written_under = (report.get("assistance_snapshot") or {}).get("assistance")
            if written_under is None:
                st.caption("Written under the faculty-reported context of its time: "
                           + ASSISTANCE.get(report["assistance_context"], report["assistance_context"]))
            else:
                st.caption("Written under: " + str(written_under.get("label")))
                current = declared.get("assistance")
                if (current or {}).get("sequence", 0) != written_under.get("sequence", 0):
                    st.info("The assistance context was declared again after this brief was "
                            "written. The brief is kept exactly as written; generate a new one to "
                            "use the current declaration, and both will remain on record.")
            if report.get("autonomy_withheld"):
                st.caption("Autonomy the declared context did not allow the AI to propose was left "
                           "for your confirmation: " + ", ".join(report["autonomy_withheld"]) + ".")
            analysis = report["analysis"]
            _pdf_download(context, report, record, compact=True, assessment=assessment)
            st.caption("Start with the 2-page brief, then review an objective below, edit its draft and record your judgment. The full analysis remains available for verification.")
            labels = _labels(record)
            correct = _prose(record)
            # The same held state the PDFs show: a negative suggestion whose
            # basis the record cannot settle waits for the faculty's reading.
            limits = findings.encounter_limits(
                ((record.get("payload") or {}).get("session") or {}).get("management_trace") or [])
            st.dataframe([
                {"Objective": key["objective_id"] + " · " + OBJECTIVES[key["objective_id"]]["title"],
                 "AI suggestion": (findings.HELD_STATUS if findings.hold_for_review(key, limits)
                                   else RECOMMENDATIONS[key["recommendation"]]),
                 "Depth": (key["depth"] or "Faculty judgment needed").capitalize(),
                 "Autonomy": ((key["autonomy"] or "").capitalize()
                              or encounter_context.AUTONOMY_NOT_DETERMINED[0])}
                for key in analysis["objectives"]
            ], hide_index=True, use_container_width=True)
            with st.expander("Read the analysis and debriefing questions"):
                _pdf_download(context, report, record, compact=False, assessment=assessment)
                st.markdown("**Performance synthesis**")
                st.write(correct(analysis["summary"]))
                for title, values in (("Strengths", analysis["strengths"]),
                                      ("Points to review", analysis["review_points"])):
                    st.markdown("**" + title + "**")
                    for value in values:
                        st.write(correct(value))
                for decision in analysis["key_decisions"]:
                    st.caption(_reference_text(decision["evidence_refs"], labels))
                    st.write(correct(decision["analysis"]))
                    st.write("Discuss: " + correct(decision["question"]))
                st.markdown("**Reflection and adaptation**")
                st.write(correct(analysis["learning_cycle"]))
                st.markdown("**Limits of this analysis**")
                for value in analysis["limits"]:
                    st.write(correct(value))
                for suggestion in analysis["objectives"]:
                    st.markdown("**" + suggestion["objective_id"] + " · " + OBJECTIVES[suggestion["objective_id"]]["title"] + "**")
                    st.write(correct(suggestion["rationale"]))
                    st.caption(_reference_text(suggestion["evidence_refs"], labels))
                    st.write(correct(suggestion["feedback"]))
                    for question in suggestion["questions"]:
                        st.write("Discuss: " + correct(question))
            st.caption("Select an objective below to load its suggestion as an editable draft. Only Record objective assessment saves your final judgment.")
    except (AccountError, FacultyAnalysisError) as exc:
        st.error(str(exc))


def render_suggestion_loader(context, record, objective_id, widget_prefix):
    """Called before form widgets are instantiated, so loading never auto-submits."""
    record = _staff_record(context, record)
    marker_key = widget_prefix + "_ai_draft"
    field_names = ("decision", "depth", "autonomy", "context", "evidence", "notes", "ack")
    marker = st.session_state.get(marker_key)
    try:
        report = _current_report(context, record)
    except AccountError as exc:
        # A report-storage failure must not relabel populated AI fields as a
        # manual assessment or bypass their acknowledgement/provenance.
        st.warning(str(exc))
        report = False
    # A draft loaded from one brief does not survive a newer brief or a changed
    # encounter: its fields came from somewhere that is no longer current.
    if marker and (marker.get("source_hash") != source_fingerprint(record)
                   or (report and marker.get("brief_id") != report.get("brief_id"))):
        for field in field_names:
            st.session_state.pop(widget_prefix + "_" + field, None)
        st.session_state.pop(marker_key, None)
        marker = None
    report = report or None
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
        correct = _prose(record)
        st.write(correct(suggestion["rationale"]))
        if suggestion.get("autonomy") is None and suggestion["recommendation"] != "insufficient_evidence":
            import encounter_context
            st.caption(encounter_context.AUTONOMY_NOT_DETERMINED[0] + ".")
        if st.button("Load AI suggestion into editable form", key=widget_prefix + "_load_ai"):
            # What is loaded becomes the faculty's draft, and a saved
            # observation is read by the resident: it arrives with the
            # identifiers already written as decisions.
            values = {
                "decision": {"satisfactory": "Satisfactory", "needs_improvement": "Needs improvement"}.get(suggestion["recommendation"]),
                "depth": suggestion["depth"], "autonomy": suggestion["autonomy"],
                "context": correct(suggestion["context"]), "evidence": list(suggestion["evidence_refs"]),
                "notes": correct(suggestion["feedback"]), "ack": False,
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
