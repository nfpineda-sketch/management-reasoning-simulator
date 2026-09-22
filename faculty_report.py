"""Faculty-only PDF presentation of an already validated AI assessment brief.

The renderer does not call a model, assign credit, save assessments, or infer new
clinical findings. Only explicit metadata and reference labels are selected
from the attempt; engine state and evidence ``details`` are never serialized.
"""

from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import re
from urllib.parse import urlencode, urlsplit, urlunsplit

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

from objectives import AUTONOMY_LEVELS, DEPTH_LEVELS, OBJECTIVES, evidence_items
from faculty_analysis import (DYNAMIC_OBJECTIVE_PROMPTS, PROMPT_VERSION,
                              SUPPORTED_OBJECTIVES, supported_objectives)


NAVY = colors.HexColor("#16324F")
BLUE = colors.HexColor("#1671A6")
ORANGE = colors.HexColor("#D57C2A")
INK = colors.HexColor("#243746")
MUTED = colors.HexColor("#63788A")
PALE = colors.HexColor("#F0F5F9")
LINE = colors.HexColor("#D8E2EB")
RECOMMENDATIONS = {
    "satisfactory": "Suggested satisfactory demonstration",
    "needs_improvement": "Suggested improvement needed",
    "insufficient_evidence": "Insufficient evidence to judge",
}
ASSISTANCE_LABELS = {
    "unknown": "Not known / not documented. Faculty must establish the assistance received before judging autonomy.",
    "guided": "Guided - structured help directed the reasoning (faculty-reported).",
    "prompted": "Prompted - additional prompts were needed (faculty-reported).",
    "independent": "Independent - faculty has verified no additional help.",
}


import record_findings as findings
import report_presentation as presentation


def _record_limits(record):
    """What this encounter's record cannot settle, read from the record."""
    session = ((record or {}).get("payload") or {}).get("session") or {}
    return findings.encounter_limits(session.get("management_trace") or [])


def _encounter_identifier(record):
    """The same visible identifier the learner report prints for this encounter."""
    session = ((record or {}).get("payload") or {}).get("session") or {}
    case_id = str(((session.get("state") or {}).get("case_id")) or "")
    return presentation.identifier(case_id, str((record or {}).get("challenge_id") or ""))


def _string(value):
    return value if isinstance(value, str) else ""


def _xml(value):
    """Make user/model text inert inside ReportLab's XML-like paragraphs."""
    text = _string(value).translate(str.maketrans(
        "₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return escape(text).replace("\n", "<br/>")


def _fonts():
    folder = Path(__file__).resolve().parent / "assets" / "fonts"
    for suffix, filename in (("", "Regular"), ("-Bold", "Bold"), ("-Italic", "Italic")):
        name = "FacultySans" + suffix
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(folder / f"LiberationSans-{filename}.ttf")))
    pdfmetrics.registerFontFamily(
        "FacultySans", normal="FacultySans", bold="FacultySans-Bold",
        italic="FacultySans-Italic", boldItalic="FacultySans-Bold")


def _styles():
    body = ParagraphStyle(
        "FacultyBody", fontName="FacultySans", fontSize=11, leading=15.2,
        textColor=INK, spaceAfter=6, splitLongWords=True, allowWidows=0,
        allowOrphans=0,
    )
    return {
        "body": body,
        "small": ParagraphStyle("FacultySmall", parent=body, fontSize=9, leading=12.2, textColor=MUTED),
        "title": ParagraphStyle("FacultyTitle", parent=body, fontName="FacultySans-Bold", fontSize=27, leading=30, textColor=NAVY, spaceAfter=9),
        "heading": ParagraphStyle("FacultyHeading", parent=body, fontName="FacultySans-Bold", fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=8, keepWithNext=True),
        "subhead": ParagraphStyle("FacultySubhead", parent=body, fontName="FacultySans-Bold", fontSize=10, leading=13, textColor=NAVY, spaceBefore=7, spaceAfter=3, keepWithNext=True),
        "eyebrow": ParagraphStyle("FacultyEyebrow", parent=body, fontName="FacultySans-Bold", fontSize=8, leading=10, textColor=BLUE, spaceAfter=6, keepWithNext=True),
        "quote": ParagraphStyle("FacultyQuote", parent=body, fontSize=10, leading=13.5, textColor=BLUE, leftIndent=9, borderColor=LINE, borderWidth=1, borderPadding=7, spaceBefore=3, spaceAfter=9),
        "status": ParagraphStyle("FacultyStatus", parent=body, fontName="FacultySans-Bold", fontSize=10.5, leading=14, textColor=BLUE, spaceAfter=6),
        "footer": ParagraphStyle("FacultyFooter", parent=body, fontSize=6.7, leading=8.6, textColor=MUTED, spaceAfter=0),
    }


def _minute(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        minute = int(value)
        return f"{minute // 60:02d}:{minute % 60:02d}"
    return "Time not recorded"


def _timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except (OverflowError, OSError, ValueError):
            pass
    return _string(value) or "Not recorded"


def _evidence_index(record):
    """Strict projection: no action summaries, states, or arbitrary dictionaries."""
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    index = {}
    for item in evidence_items(payload):
        details = item.get("details", {})
        time = _minute(details.get("decision_time_min")) if item["kind"] == "decision" else "Post-encounter reflection"
        index[item["ref"]] = {
            "label": _string(item.get("label")), "time": time,
            "input": _string(details.get("learner_input")) if item["kind"] == "decision" else "",
        }
    return index


def _validated_inputs(report, record):
    if not isinstance(report, dict) or report.get("schema_version") != "faculty_brief_v1":
        raise ValueError("A validated faculty brief is required.")
    if not isinstance(record, dict) or report.get("attempt_id") != record.get("id"):
        raise ValueError("The faculty brief belongs to a different encounter.")
    if report.get("attempt_revision") != record.get("revision"):
        raise ValueError("The faculty brief belongs to a different encounter revision.")
    analysis = report.get("analysis")
    if not isinstance(analysis, dict):
        raise ValueError("The faculty brief has no analysis.")
    objectives = analysis.get("objectives", [])
    supported = list(supported_objectives(record) if report.get("prompt_version") in DYNAMIC_OBJECTIVE_PROMPTS
                     else SUPPORTED_OBJECTIVES)
    if not isinstance(objectives, list) or len(objectives) != len(supported) or {
        item.get("objective_id") for item in objectives if isinstance(item, dict)
    } != set(supported):
        raise ValueError("The faculty brief must address each supported objective once.")
    index = _evidence_index(record)
    decisions = analysis.get("key_decisions", [])
    for item in list(decisions) + objectives:
        if not isinstance(item, dict) or not isinstance(item.get("evidence_refs"), list):
            raise ValueError("Faculty evidence references are invalid.")
        if any(not isinstance(ref, str) or ref not in index for ref in item["evidence_refs"]):
            raise ValueError("A cited faculty evidence reference is unavailable.")
    if any(item.get("recommendation") not in RECOMMENDATIONS for item in objectives):
        raise ValueError("The faculty recommendation is invalid.")

    return analysis, objectives, supported, index, decisions


def _render_full(report, record, inputs, correct=None):
    """Preserve the complete stored analysis, allowing paragraphs to flow."""
    analysis, objectives, supported, index, decisions = inputs
    _fonts()
    styles = _styles()
    out = BytesIO()
    width, height = A4
    margin = 42
    content_width = width - 2 * margin
    document = SimpleDocTemplate(
        out, pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=51, bottomMargin=64,
        title="Faculty Assessment Brief", author="Management Reasoning Simulator",
        subject="AI-generated decision support for faculty review",
        pageCompression=1,
    )
    story = []
    correct = correct or presentation.CorrectionLog()

    def p(value, style="body"):
        return Paragraph(_xml(correct(value)), styles[style])

    def section(title, text):
        story.append(p(title, "subhead"))
        story.append(p(text))

    def bullets(values, limits=None):
        for value in values if isinstance(values, list) else []:
            written = correct(value)
            story.append(Paragraph("<b>•</b> " + _xml(written), styles["body"]))
            caveat = findings.unsettled(written, limits) if limits else []
            if caveat:
                story.append(p("Ask this rather than judge it: " + caveat[0] + ".", "small"))

    def reference_text(refs):
        return "; ".join(f"{index[ref]['label']} | {index[ref]['time']} [{ref}]" for ref in refs)

    def page_header(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(margin, height - 33, width - margin, height - 33)
        canvas.setFont("FacultySans-Bold", 7.4)
        canvas.setFillColor(NAVY)
        canvas.drawString(margin, height - 25, "MANAGEMENT REASONING SIMULATOR")
        canvas.setFillColor(BLUE)
        canvas.drawRightString(width - margin, height - 25, "FACULTY REVIEW • AI DRAFT")
        canvas.setStrokeColor(LINE)
        canvas.line(margin, 53, width - margin, 53)
        footer = p(
            f"AI draft - faculty judgment required | Model: {_string(report.get('model'))} | "
            f"Generated: {_timestamp(report.get('generated_at'))}\n"
            f"Encounter revision {report.get('attempt_revision')} | Source: {_string(report.get('source_hash'))}",
            "footer",
        )
        _, footer_height = footer.wrap(content_width - 28, 38)
        footer.drawOn(canvas, margin, 47 - footer_height)
        canvas.setFont("FacultySans", 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(width - margin, 31, str(doc.page))
        canvas.restoreState()

    story.append(p("ENCOUNTER ASSESSMENT SUPPORT", "eyebrow"))
    story.append(p("Faculty Assessment Brief", "title"))
    story.append(p("AI-generated interpretation for faculty review. Suggestions remain provisional until the faculty member reviews the evidence and records a judgment.", "body"))
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    state = session.get("state") if isinstance(session.get("state"), dict) else {}
    case_id = _string(state.get("case_id")) or _string(session.get("selected_case")) or "Not recorded"
    rows = [
        [p("RESIDENT", "eyebrow"), p("ENCOUNTER", "eyebrow"), p("COMPLETED RECORD", "eyebrow")],
        [p(_string(record.get("username"))), p(_encounter_identifier(record)), p(_timestamp(record.get("updated_at")))],
    ]
    metadata = Table(rows, colWidths=[content_width * .3, content_width * .3, content_width * .4])
    metadata.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 0), ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
    ]))
    story.extend([metadata, Spacer(1, 9)])
    section("Performance synthesis", analysis.get("summary"))
    section("Assistance context", ASSISTANCE_LABELS.get(
        _string(report.get("assistance_context")), ASSISTANCE_LABELS["unknown"]))
    story.append(p("Strengths supported by the record", "subhead"))
    bullets(analysis.get("strengths"))
    story.append(p("Points for faculty review", "subhead"))
    bullets(analysis.get("review_points"), _record_limits(record))
    section("Reasoning during the encounter and later reflection", analysis.get("learning_cycle"))

    story.append(PageBreak())
    story.append(p("DECISION REVIEW", "eyebrow"))
    story.append(p("Evidence to discuss", "heading"))
    story.append(p("Blue excerpts reproduce the learner's recorded words. The analysis and questions are AI interpretations to verify against the complete Management Trace.", "small"))
    for number, item in enumerate(decisions, 1):
        refs = item["evidence_refs"]
        first = next((index[ref] for ref in refs if index[ref]["input"]), None)
        block = [p(f"{number:02d} | {reference_text(refs) or 'No cited decision'}", "subhead"),
                 p("AI interpretation", "eyebrow"), p(item.get("analysis"))]
        if first:
            source = first["input"]
            excerpt = source if len(source) <= 450 else source[:450].rsplit(" ", 1)[0] + " [...]"
            block.append(p(f"Recorded learner excerpt - {first['label']}: {excerpt}", "quote"))
        block.extend([p("Debrief question", "subhead"), p(item.get("question")),
                      Spacer(1, 5), HRFlowable(width="100%", thickness=.6, color=LINE), Spacer(1, 6)])
        story.append(KeepTogether(block))

    # One objective is one block. The former rule of two per page forced a
    # break that left an empty page and stranded the tail of an objective on a
    # page of its own once the text grew (faculty review 2026-09-23).
    ordered = {item["objective_id"]: item for item in objectives}
    limits = _record_limits(record)
    story.append(PageBreak())
    story.append(p("PROVISIONAL OBJECTIVE ASSESSMENTS", "eyebrow"))
    story.append(p("Review, edit and record", "heading"))
    for position, objective_id in enumerate(supported):
        if position:
            story.extend([Spacer(1, 13), HRFlowable(width="100%", thickness=1, color=LINE), Spacer(1, 9)])
        item = ordered[objective_id]
        catalog = OBJECTIVES[objective_id]
        recommendation = item["recommendation"]
        depth = item.get("depth")
        autonomy = item.get("autonomy")
        label_style = ParagraphStyle(
            f"FacultyStatus{position}", parent=styles["status"],
            textColor=ORANGE if recommendation == "needs_improvement" else (
                MUTED if recommendation == "insufficient_evidence" else BLUE),
        )
        # An objective with no evidence anchor at all had no recorded chance to
        # be shown; that is different from a weak demonstration (2026-09-23).
        no_opportunity = (recommendation == "insufficient_evidence"
                          and not [ref for ref in item.get("evidence_refs", []) if ref])
        # A negative suggestion the record cannot settle is held for the faculty
        # rather than shown as a judgment; the suggestion itself is preserved.
        held = findings.hold_for_review(item, limits)
        if held:
            label_style = ParagraphStyle(f"FacultyHeld{position}", parent=styles["status"], textColor=MUTED)
        block = [
            p(f"{objective_id} | {catalog['title']}", "subhead"),
            Paragraph(_xml(findings.HELD_STATUS if held else
                           "Not assessed in this encounter - no recorded opportunity to demonstrate it"
                           if no_opportunity else RECOMMENDATIONS[recommendation]), label_style),
            p(catalog["scope"], "small"),]
        if held:
            block += [
                p("AI suggestion on record: " + RECOMMENDATIONS[recommendation]
                  + ". It is held for your reading because " + held[0]
                  + ". No new rating was assigned and no recorded faculty judgment was changed.", "small"),
            ]
        block += [
            p("AI rationale", "subhead"), p(item.get("rationale")),
            p(f"Suggested depth: {depth.capitalize() if depth in DEPTH_LEVELS else 'Needs faculty judgment'} | "
              f"Suggested autonomy: {autonomy.capitalize() if autonomy in AUTONOMY_LEVELS else 'Needs faculty judgment'}",
              "small"),
            p("Observed context", "subhead"), p(item.get("context")),
            p("Recorded evidence to inspect", "subhead"),
            p(reference_text(item["evidence_refs"]) or "No supporting references were selected. Do not infer an observed skill from absence of evidence."),
            p("Feedback draft - editable in the app", "subhead"), p(item.get("feedback")),
        ]
        if item.get("questions"):
            block.append(p("Questions before recording", "subhead"))
            block += [Paragraph("<b>•</b> " + _xml(correct(value)), styles["body"])
                      for value in item.get("questions") if isinstance(item.get("questions"), list)]
        block.append(p("Scope limit: " + catalog["limitation"], "small"))
        if catalog.get("competency_mapping"):
            block.append(p("Competency correspondence · local simulated evidence", "subhead"))
            for mapping in catalog["competency_mapping"]:
                label = mapping["framework"] + " · " + mapping["code"]
                block.append(Paragraph('<link href="' + escape(mapping["source_url"], {'"': '&quot;'})
                    + '">' + _xml(label) + '</link>', styles["small"]))
                block.append(p(mapping.get("source_locator", ""), "small"))
        story.append(KeepTogether(block))

    # The limits of the analysis close the document with its metadata rather
    # than stranding the tail of the first section on a page of its own.
    story.extend([Spacer(1, 12), HRFlowable(width="100%", thickness=.6, color=LINE), Spacer(1, 5)])
    story.append(p("Interpretation limits", "subhead"))
    bullets(analysis.get("limits"))
    story.append(p("This brief does not save an assessment, add observations, or confirm an objective. Only the supported simulated components are considered.", "small"))
    story.append(Spacer(1, 8))
    story.append(p("Generation record", "subhead"))
    story.append(p(
        f"Encounter: {_encounter_identifier(record)}\n"
        f"Attempt ID: {_string(report.get('attempt_id'))}\n"
        f"Source revision: {report.get('attempt_revision')} | Schema: {_string(report.get('schema_version'))} | "
        f"Prompt version: {_string(report.get('prompt_version'))}", "small"))
    if correct.applied:
        story.append(p(f"{len(correct.applied)} factual correction(s) were applied to the AI text at render "
                       "time; the stored brief keeps the original wording.", "small"))
        for reason in correct.lines():
            story.append(p("Correction: " + reason, "small"))
    document.build(story, onFirstPage=page_header, onLaterPages=page_header)
    return out.getvalue()


_COMPACT_RECOMMENDATIONS = {
    "satisfactory": "Satisfactory",
    "needs_improvement": "Needs improvement",
    "insufficient_evidence": "Insufficient evidence",
}
_COMPACT_TITLES = {
    "TD1": "Recognize instability",
    "F1": "Initiate resuscitation",
    "C1": "Manage resuscitation",
    "C3": "Airway and ventilation",
    "C4": "Procedural sedation",
    "C14": "POCUS in management",
    "R1-05": "Reconsider the initial model",
    "R1-06": "Keep alternatives open",
    "R2-02": "Seek discordant evidence",
    "R2-03": "Weigh the current evidence",
    "R1-07": "Reassess the handover frame",
    "R2-04": "Recognize atypical illness",
    "R2-05": "Look beyond the first finding",
    "R3-01": "Justify action or observation",
}


def _sentence_excerpt(value, limit, fallback, *, maximum_sentences=None):
    """Select complete initial sentences; never turn a partial clause into a claim.

    A very long first sentence cannot be compressed without interpreting it.
    In that case the reader is directed to the complete source in the app.
    All compact sections are explicitly presented as selected excerpts.
    """
    value = " ".join(_string(value).split())
    value = value.replace("airway_prepared remained false", "airway preparation was not marked as completed")
    if len(value) <= limit and maximum_sentences is None:
        return value or fallback
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ0-9\"'])", value)
    selected = []
    for sentence in sentences:
        if len(" ".join(selected + [sentence])) > limit:
            break
        selected.append(sentence)
        if maximum_sentences is not None and len(selected) >= maximum_sentences:
            break
    # No safe first complete sentence fits; do not select a later sentence that
    # might reverse the meaning or depend on context that has been omitted.
    return " ".join(selected) if selected else fallback


def _encounter_url(app_url, attempt_id):
    if not app_url:
        return None
    if not isinstance(app_url, str):
        raise ValueError("The faculty app URL must be a public HTTP(S) URL.")
    parts = urlsplit(app_url)
    if (parts.scheme not in {"http", "https"} or not parts.hostname
            or parts.username is not None or parts.password is not None):
        raise ValueError("The faculty app URL must be a public HTTP(S) URL without credentials.")
    # The destination is a selector, never an authorization token. Discard all
    # supplied query parameters/fragments, which may contain session secrets.
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/",
                       urlencode({"faculty_attempt": attempt_id}), ""))


def _compact_references(refs, index, maximum=3):
    anchors = []
    for ref in refs[:maximum]:
        item = index[ref]
        if ref.startswith("trace:"):
            anchors.append(f"D{int(ref.split(':', 1)[1]) + 1} {item['time']}")
        else:
            label = item["label"].replace("Reflection ", "Reflection ")
            anchors.append(label)
    if len(refs) > maximum:
        anchors.append(f"+{len(refs) - maximum} in app")
    return " · ".join(anchors) or "No supporting reference selected"


def _render_compact(report, record, inputs, app_url, correct=None):
    """Two-page reading route through an unchanged, optionally verbose report.

    The matrix does not replace the rationale, feedback or complete decision
    review. Excerpt selection is deterministic and visibly disclosed; only
    the faculty member may resolve limitations and record an assessment.
    """
    analysis, objectives, supported, index, decisions = inputs
    destination = _encounter_url(app_url, report["attempt_id"])
    encounter_id = _encounter_identifier(record)
    limits = _record_limits(record)
    _fonts()
    out = BytesIO()
    width, height = A4
    margin = 38
    usable = width - 2 * margin
    base = ParagraphStyle(
        "CompactBody", fontName="FacultySans", fontSize=11, leading=14.5,
        textColor=INK, spaceAfter=0, allowWidows=0, allowOrphans=0,
    )
    styles = {
        "body": base,
        "muted": ParagraphStyle("CompactMuted", parent=base, fontSize=9.4, leading=12.6, textColor=MUTED),
        "bold": ParagraphStyle("CompactBold", parent=base, fontName="FacultySans-Bold", textColor=NAVY),
        "title": ParagraphStyle("CompactTitle", parent=base, fontName="FacultySans-Bold", fontSize=25, leading=28, textColor=NAVY, spaceAfter=6),
        "heading": ParagraphStyle("CompactHeading", parent=base, fontName="FacultySans-Bold", fontSize=14, leading=17, textColor=NAVY, spaceBefore=5, spaceAfter=7),
        "label": ParagraphStyle("CompactLabel", parent=base, fontName="FacultySans-Bold", textColor=BLUE, spaceAfter=4),
    }

    correct = correct or presentation.CorrectionLog()

    def p(text, style="body"):
        return Paragraph(_xml(correct(text)), styles[style])

    document = SimpleDocTemplate(
        out, pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=48, bottomMargin=45,
        title="Faculty Assessment Brief - concise review",
        author="Management Reasoning Simulator",
        subject="Selected evidence and provisional suggestions for faculty review",
        pageCompression=1,
    )

    def page_frame(canvas, doc, total=None):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(margin, height - 34, width - margin, height - 34)
        canvas.setFillColor(NAVY)
        canvas.setFont("FacultySans-Bold", 8)
        canvas.drawString(margin, height - 25, "MANAGEMENT REASONING SIMULATOR")
        canvas.setFillColor(BLUE)
        canvas.drawRightString(width - margin, height - 25, "FACULTY REVIEW · AI DRAFT")
        canvas.setStrokeColor(LINE)
        canvas.line(margin, 34, width - margin, 34)
        canvas.setFont("FacultySans", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(margin, 22, f"{encounter_id} · revision {report.get('attempt_revision')} · Faculty judgment required")
        canvas.drawRightString(width - margin, 22, f"{doc.page} / {total}" if total else str(doc.page))
        canvas.restoreState()

    def box(text, background=PALE, accent=BLUE):
        element = Table([[p(text)]], colWidths=[usable])
        element.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), background),
            ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
            ("LEFTPADDING", (0, 0), (-1, -1), 11),
            ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return element

    def call_to_action():
        if destination:
            label = Paragraph(
                '<link href="' + escape(destination, {'"': '&quot;'}) +
                '" color="#FFFFFF"><b>Open this encounter → review and record your assessment</b></link>',
                styles["body"],
            )
            element = Table([[label]], colWidths=[usable])
            element.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            return element
        return box("In the app: open this encounter, inspect the evidence, then edit and save each objective assessment.")

    def review_page(review_limit, question_limit):
        """Page one: the synthesis, the concerns and the prompts to debrief with.

        Faculty request 2026-09-23: the suggested ratings are read last, after
        the evidence they rest on, so that reading the brief is reviewing the
        encounter rather than accepting a verdict.
        """
        story = [p("Faculty Assessment Brief", "title")]
        story.append(p(f"{_string(record.get('username'))}  |  {encounter_id}  |  {_timestamp(record.get('updated_at'))}", "muted"))
        story.extend([Spacer(1, 10),
                      p("1  Read the synthesis and concerns  ·  2  Check the evidence  ·  3  Record your judgment", "bold"),
                      Spacer(1, 8)])
        story.append(p("Performance synthesis", "heading"))
        summary = _sentence_excerpt(correct(analysis.get("summary")), max(review_limit, 320),
                                    "Read the full synthesis in the app before judging this encounter.")
        story.append(p(summary))
        story.append(Spacer(1, 4))
        assistance = ASSISTANCE_LABELS.get(_string(report.get("assistance_context")), ASSISTANCE_LABELS["unknown"])
        story.append(p("AI draft. Every suggestion in this brief stays provisional until you record your own "
                       "judgment. Assistance and autonomy: " + assistance, "muted"))
        review_points = analysis.get("review_points", [])
        review_points = review_points if isinstance(review_points, list) else []
        story.extend([Spacer(1, 7), p(f"{min(3, len(review_points))} selected review priorities", "heading")])
        for number, point in enumerate(review_points[:3], 1):
            excerpt = _sentence_excerpt(correct(point), review_limit, "Read this review point in full in the app; its context cannot be safely shortened here.")
            # A concern the record cannot settle is asked, not asserted.
            caveat = findings.unsettled(excerpt, limits)
            cell = [p(excerpt)]
            if caveat:
                cell.append(p("Ask this rather than judge it: " + caveat[0] + ".", "muted"))
            table = Table([[p(f"0{number}", "label"), cell]], colWidths=[31, usable - 31])
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FCF5ED")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.extend([table, Spacer(1, 6)])
        if len(review_points) > 3:
            story.append(p(f"First 3 of {len(review_points)} review points, in the analysis's original order. Read the remaining {len(review_points) - 3} in the full analysis before finalizing.", "muted"))
        if not review_points:
            story.append(p("No review points were provided. Verify the source evidence before accepting any suggestion.", "muted"))
        story.extend([Spacer(1, 7), p("Focused debrief prompts", "heading")])
        for item in decisions[:3]:
            question = _sentence_excerpt(correct(item.get("question")), question_limit, "Review this decision's full debrief question in the app.")
            story.append(KeepTogether([
                p(_compact_references(item["evidence_refs"], index, maximum=2), "label"),
                p(question), Spacer(1, 8),
            ]))
        if len(decisions) > 3:
            story.append(p(f"3 of {len(decisions)} decision prompts shown; full analysis contains the rest.", "muted"))
        return story

    def assessments_page(rationale_limit):
        """Page two: the provisional suggestions, then the scope and provenance."""
        story = [p("Suggested assessments", "title"),
                 p("AI suggestions are provisional; documented factual corrections have been applied. "
                   "Resolve the concerns on page 1 before accepting a suggestion; the rationale excerpts "
                   "and evidence anchors are a reading aid.", "muted"),
                 Spacer(1, 7)]
        ordered = {item["objective_id"]: item for item in objectives}
        columns = [usable * .20, usable * .195, usable * .605]
        # A concise brief is for directing attention. An objective suggested as
        # satisfactory and settled by the record takes one line, and its
        # rationale is read in the complete PDF; everything that needs the
        # faculty to decide keeps its full row (faculty request 2026-09-23).
        def needs_attention(objective_id):
            item = ordered[objective_id]
            return bool(findings.hold_for_review(item, limits)) or item["recommendation"] != "satisfactory"

        attention = [key for key in supported if needs_attention(key)]
        settled = [key for key in supported if not needs_attention(key)]
        rows = [[p("OBJECTIVE", "bold"), p("AI SUGGESTION", "bold"), p("RATIONALE EXCERPT · EVIDENCE", "bold")]]
        for objective_id in attention:
            item = ordered[objective_id]
            depth = item.get("depth")
            recommendation = item["recommendation"]
            # An objective the encounter never gave a chance to show is not the
            # same as one shown weakly: with no evidence anchor at all, the
            # honest label is that it was not assessed here.
            no_opportunity = (recommendation == "insufficient_evidence"
                              and not [ref for ref in item.get("evidence_refs", []) if ref])
            held = findings.hold_for_review(item, limits)
            status_style = ParagraphStyle(
                "CompactStatus" + objective_id, parent=styles["bold"],
                textColor=MUTED if held or recommendation == "insufficient_evidence" else (
                    ORANGE if recommendation == "needs_improvement" else BLUE),
            )
            status_text = (findings.HELD_STATUS if held
                           else "Not assessed in this encounter" if no_opportunity
                           else _COMPACT_RECOMMENDATIONS[recommendation])
            depth_text = ("AI suggested " + _COMPACT_RECOMMENDATIONS[recommendation].lower() if held
                          else "No recorded opportunity" if no_opportunity
                          else "Depth: " + (depth.capitalize() if depth in DEPTH_LEVELS else "To establish"))
            rationale = _sentence_excerpt(
                correct(item.get("rationale")), rationale_limit,
                "Review the full rationale in the app before judging this objective.",
                maximum_sentences=1,
            )
            if held:
                # The status already says it is held; the row carries the reason.
                rationale += " Held because " + held[0] + "."
            rows.append([
                [p(objective_id, "label"), p(_COMPACT_TITLES.get(objective_id, OBJECTIVES[objective_id]["title"]))],
                [Paragraph(_xml(status_text), status_style), Spacer(1, 4), p(depth_text, "muted")],
                [p(rationale), Spacer(1, 5), p(_compact_references(item["evidence_refs"], index), "muted")],
            ])
        matrix = Table(rows, colWidths=columns, repeatRows=1, hAlign="LEFT")
        matrix.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), .8, LINE),
            ("LINEBELOW", (0, 1), (-1, -1), .5, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.extend([matrix, Spacer(1, 6)])
        if settled:
            story.append(p("Suggested satisfactory, and settled by the record", "label"))
            story.append(p("One line each; the rationale and the evidence for these are in the complete "
                           "PDF and in the app. They still need your judgment to be recorded.", "muted"))
            for objective_id in settled:
                item = ordered[objective_id]
                depth = item.get("depth")
                depth_text = depth.capitalize() if depth in DEPTH_LEVELS else "To establish"
                anchors = _compact_references(item["evidence_refs"], index, maximum=3)
                story.append(Paragraph(
                    "<b>" + _xml(objective_id) + "</b> · "
                    + _xml(_COMPACT_TITLES.get(objective_id, OBJECTIVES[objective_id]["title"]))
                    + " — " + _xml(_COMPACT_RECOMMENDATIONS[item["recommendation"]])
                    + " · " + _xml(depth_text) + (" · " + _xml(anchors) if anchors else ""),
                    styles["body"]))
            story.append(Spacer(1, 6))
        # Scope, the report's own limit and the route back to the app close the
        # reading page, where there is room for them.
        story.append(p("What this encounter can and cannot show", "heading"))
        story.append(p("Recorded reasoning under simulation: not teamwork, hands-on airway or procedural "
                       "skill, and not image acquisition. A local observation awards no Milestone level or "
                       "EPA. Scope per objective and competency correspondence are in the complete PDF.", "muted"))
        analysis_limits = analysis.get("limits", [])
        if isinstance(analysis_limits, list):
            distinct_limit = next((value for value in analysis_limits
                                   if not re.search(r"assistance|autonomy", _string(value), re.I)), None)
            if distinct_limit:
                story.append(Spacer(1, 3))
                story.append(p("Selected analysis limit: " + _sentence_excerpt(
                    distinct_limit, 250, "Review the analysis-specific limits in the app."), "muted"))
        story.extend([Spacer(1, 8), call_to_action(), Spacer(1, 5)])
        tail = ("D = recorded decision and simulation time. Reflection = post-encounter evidence and does not "
                "establish what was understood during care. Suggestions add no credit and save no assessment. "
                f"Encounter {encounter_id} · revision {report.get('attempt_revision')} · "
                f"{_string(report.get('model'))}. Full generation record, citations and rationales in the complete PDF.")
        if correct.applied:
            tail += f" {len(correct.applied)} factual correction(s) applied to the AI text; the stored brief keeps the original wording."
        story.append(p(tail, "muted"))
        return story

    def page_height(elements):
        total = 0
        for element in elements:
            if isinstance(element, KeepTogether):
                total += page_height(element._content)
            else:
                _, element_height = element.wrap(usable - 12, height)
                total += element_height + element.getSpaceBefore() + element.getSpaceAfter()
        return total

    # Fit by choosing fewer complete source sentences, never by shrinking the
    # font or clipping a paragraph. Oversized first sentences become explicit
    # review cues, and the full report continues to retain every character.
    # The first page is fitted by choosing fewer complete source sentences,
    # never by shrinking the font or clipping a paragraph.
    available = height - document.topMargin - document.bottomMargin - 12
    # The suggestion page is built first: it is where most corrections land, and
    # the first page reports how many were applied.
    page_two = assessments_page(520)
    for rationale_limit in (520, 430, 390, 330, 300, 275):
        candidate = assessments_page(rationale_limit)
        page_two = candidate
        if page_height(candidate) <= available:
            break
    for review_limit, question_limit in ((550, 300), (400, 250), (300, 200), (200, 150), (90, 90)):
        page_one = review_page(review_limit, question_limit)
        if page_height(page_one) <= available:
            break
    if page_height(page_one) > available:
        raise ValueError("This report metadata is too long for the concise PDF; download the full analysis.")
    # The suggestion matrix keeps its rationale and flows onto a further page if
    # it needs one (faculty request 2026-09-23: readable text first, and a
    # rationale replaced by "read it in the app" is not a reading aid). The
    # table repeats its header row, so a split reads correctly.
    story = page_one + [PageBreak()] + page_two

    def build(counter):
        buffer = BytesIO()
        pages = SimpleDocTemplate(
            buffer, pagesize=A4, leftMargin=margin, rightMargin=margin,
            topMargin=48, bottomMargin=45,
            title="Faculty Assessment Brief - concise review",
            author="Management Reasoning Simulator",
            subject="Selected evidence and provisional suggestions for faculty review",
            pageCompression=1,
        )
        frame = lambda canvas, doc: page_frame(canvas, doc, counter)
        pages.build(deepcopy(story), onFirstPage=frame, onLaterPages=frame)
        return buffer.getvalue(), pages.page

    _, total = build(None)
    return build(total)[0]


def render_faculty_brief_pdf(report, record, *, compact=True, app_url=None, corrections=None):
    """Render an unchanged stored brief as a concise review or the full report.

    The default is a two-page reading aid. ``compact=False`` retains complete
    model text and lets it flow across pages. The optional public ``app_url``
    adds an encounter selector link; authentication remains enforced by the app.
    """
    inputs = _validated_inputs(report, record)
    # Recorded factual corrections are applied to the model's text at render
    # time; the stored brief keeps the original wording (2026-09-23).
    import report_corrections
    correct = presentation.CorrectionLog(
        corrections if corrections is not None else report_corrections.for_record(record))
    if compact:
        return _render_compact(report, record, inputs, app_url, correct)
    return _render_full(report, record, inputs, correct)
