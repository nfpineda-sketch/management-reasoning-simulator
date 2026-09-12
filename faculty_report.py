"""Faculty-only PDF presentation of an already validated AI assessment brief.

The renderer does not call a model, assign credit, save assessments, or infer new
clinical findings. Only explicit metadata and reference labels are selected
from the attempt; engine state and evidence ``details`` are never serialized.
"""

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import re

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
        "FacultyBody", fontName="FacultySans", fontSize=9.3, leading=13.1,
        textColor=INK, spaceAfter=6, splitLongWords=True, allowWidows=0,
        allowOrphans=0,
    )
    return {
        "body": body,
        "small": ParagraphStyle("FacultySmall", parent=body, fontSize=8, leading=10.8, textColor=MUTED),
        "title": ParagraphStyle("FacultyTitle", parent=body, fontName="FacultySans-Bold", fontSize=27, leading=30, textColor=NAVY, spaceAfter=9),
        "heading": ParagraphStyle("FacultyHeading", parent=body, fontName="FacultySans-Bold", fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=8, keepWithNext=True),
        "subhead": ParagraphStyle("FacultySubhead", parent=body, fontName="FacultySans-Bold", fontSize=10, leading=13, textColor=NAVY, spaceBefore=7, spaceAfter=3, keepWithNext=True),
        "eyebrow": ParagraphStyle("FacultyEyebrow", parent=body, fontName="FacultySans-Bold", fontSize=8, leading=10, textColor=BLUE, spaceAfter=6, keepWithNext=True),
        "quote": ParagraphStyle("FacultyQuote", parent=body, fontSize=8.5, leading=11.5, textColor=BLUE, leftIndent=9, borderColor=LINE, borderWidth=1, borderPadding=7, spaceBefore=3, spaceAfter=9),
        "status": ParagraphStyle("FacultyStatus", parent=body, fontName="FacultySans-Bold", fontSize=9, leading=12, textColor=BLUE, spaceAfter=6),
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


def render_faculty_brief_pdf(report, record):
    """Return PDF bytes for one stored ``faculty_brief_v1`` report and attempt.

    Access control and source-hash validation belong to the faculty service/UI.
    Identity/revision and cited-reference checks here prevent mixing records
    even if the renderer is called directly. Text can split across pages; long
    model feedback is preserved instead of silently clipped or truncated.
    """
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
    supported = [key for key, entry in OBJECTIVES.items() if entry["supported"]]
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

    def p(value, style="body"):
        return Paragraph(_xml(value), styles[style])

    def section(title, text):
        story.append(p(title, "subhead"))
        story.append(p(text))

    def bullets(values):
        for value in values if isinstance(values, list) else []:
            story.append(Paragraph("<b>•</b> " + _xml(value), styles["body"]))

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
        [p(_string(record.get("username"))), p(f"{_string(record.get('challenge_id'))} | {case_id}"), p(_timestamp(record.get("updated_at")))],
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
    bullets(analysis.get("review_points"))
    section("Reasoning during the encounter and later reflection", analysis.get("learning_cycle"))
    story.append(p("Interpretation limits", "subhead"))
    bullets(analysis.get("limits"))
    story.append(p("This brief does not save an assessment, add observations, or confirm an objective. Only the supported simulated components are considered.", "small"))
    story.extend([Spacer(1, 7), HRFlowable(width="100%", thickness=.6, color=LINE), Spacer(1, 5)])
    story.append(p("Generation record", "subhead"))
    story.append(p(
        f"Attempt ID: {_string(report.get('attempt_id'))}\n"
        f"Source revision: {report.get('attempt_revision')} | Schema: {_string(report.get('schema_version'))} | "
        f"Prompt version: {_string(report.get('prompt_version'))}", "small"))

    story.append(PageBreak())
    story.append(p("DECISION REVIEW", "eyebrow"))
    story.append(p("Evidence to discuss", "heading"))
    story.append(p("Blue excerpts reproduce the learner's recorded words. The analysis and questions are AI interpretations to verify against the complete Management Trace.", "small"))
    for number, item in enumerate(decisions, 1):
        refs = item["evidence_refs"]
        first = next((index[ref] for ref in refs if index[ref]["input"]), None)
        heading = p(f"{number:02d} | {reference_text(refs) or 'No cited decision'}", "subhead")
        story.extend([heading, p("AI interpretation", "eyebrow"), p(item.get("analysis"))])
        if first:
            source = first["input"]
            excerpt = source if len(source) <= 450 else source[:450].rsplit(" ", 1)[0] + " [...]"
            story.append(p(f"Recorded learner excerpt - {first['label']}: {excerpt}", "quote"))
        story.append(p("Debrief question", "subhead"))
        story.append(p(item.get("question")))
        story.extend([Spacer(1, 5), HRFlowable(width="100%", thickness=.6, color=LINE), Spacer(1, 6)])

    # Two objectives per planned page keep the usual six-objective brief at
    # five pages. Long paragraphs flow naturally onto additional pages.
    ordered = {item["objective_id"]: item for item in objectives}
    for position, objective_id in enumerate(supported):
        if position % 2 == 0:
            story.append(PageBreak())
            story.append(p("PROVISIONAL OBJECTIVE ASSESSMENTS", "eyebrow"))
            story.append(p("Review, edit and record", "heading"))
        else:
            story.extend([Spacer(1, 15), HRFlowable(width="100%", thickness=1, color=LINE), Spacer(1, 10)])
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
        story.append(KeepTogether([
            p(f"{objective_id} | {catalog['title']}", "subhead"),
            Paragraph(_xml(RECOMMENDATIONS[recommendation]), label_style),
            p(catalog["scope"], "small"),
        ]))
        section("AI rationale", item.get("rationale"))
        story.append(p(
            f"Suggested depth: {depth.capitalize() if depth in DEPTH_LEVELS else 'Needs faculty judgment'} | "
            f"Suggested autonomy: {autonomy.capitalize() if autonomy in AUTONOMY_LEVELS else 'Needs faculty judgment'}",
            "small",
        ))
        section("Observed context", item.get("context"))
        section("Recorded evidence to inspect", reference_text(item["evidence_refs"]) or "No supporting references were selected. Do not infer an observed skill from absence of evidence.")
        section("Feedback draft - editable in the app", item.get("feedback"))
        if item.get("questions"):
            story.append(p("Questions before recording", "subhead"))
            bullets(item.get("questions"))
        story.append(p("Scope limit: " + catalog["limitation"], "small"))

    document.build(story, onFirstPage=page_header, onLaterPages=page_header)
    return out.getvalue()
