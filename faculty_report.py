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

    return analysis, objectives, supported, index, decisions


def _render_full(report, record, inputs):
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


def _render_compact(report, record, inputs, app_url):
    """Two-page reading route through an unchanged, optionally verbose report.

    The matrix does not replace the rationale, feedback or complete decision
    review. Excerpt selection is deterministic and visibly disclosed; only
    the faculty member may resolve limitations and record an assessment.
    """
    analysis, objectives, supported, index, decisions = inputs
    destination = _encounter_url(app_url, report["attempt_id"])
    _fonts()
    out = BytesIO()
    width, height = A4
    margin = 38
    usable = width - 2 * margin
    base = ParagraphStyle(
        "CompactBody", fontName="FacultySans", fontSize=9.3, leading=12,
        textColor=INK, spaceAfter=0, allowWidows=0, allowOrphans=0,
    )
    styles = {
        "body": base,
        "muted": ParagraphStyle("CompactMuted", parent=base, textColor=MUTED),
        "bold": ParagraphStyle("CompactBold", parent=base, fontName="FacultySans-Bold", textColor=NAVY),
        "title": ParagraphStyle("CompactTitle", parent=base, fontName="FacultySans-Bold", fontSize=25, leading=28, textColor=NAVY, spaceAfter=6),
        "heading": ParagraphStyle("CompactHeading", parent=base, fontName="FacultySans-Bold", fontSize=14, leading=17, textColor=NAVY, spaceBefore=5, spaceAfter=7),
        "label": ParagraphStyle("CompactLabel", parent=base, fontName="FacultySans-Bold", textColor=BLUE, spaceAfter=4),
    }

    def p(text, style="body"):
        return Paragraph(_xml(text), styles[style])

    document = SimpleDocTemplate(
        out, pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=48, bottomMargin=45,
        title="Faculty Assessment Brief - concise review",
        author="Management Reasoning Simulator",
        subject="Selected evidence and provisional suggestions for faculty review",
        pageCompression=1,
    )

    def page_frame(canvas, doc):
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
        canvas.drawString(margin, 22, f"{_string(record.get('challenge_id'))} · revision {report.get('attempt_revision')} · Faculty judgment required")
        canvas.drawRightString(width - margin, 22, f"{doc.page} / 2")
        canvas.restoreState()

    def box(text, background=PALE, accent=BLUE):
        element = Table([[p(text)]], colWidths=[usable])
        element.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), background),
            ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
            ("LEFTPADDING", (0, 0), (-1, -1), 11),
            ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
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

    def first_page(rationale_limit):
        story = [p("Faculty Assessment Brief", "title")]
        story.append(p(f"{_string(record.get('username'))}  |  {_string(record.get('challenge_id'))}  |  {_timestamp(record.get('updated_at'))}", "muted"))
        story.extend([Spacer(1, 10), p("1  Review suggestions     2  Check the concerns     3  Record your judgment", "bold"), Spacer(1, 8)])
        story.append(p("Suggested assessments", "heading"))
        story.append(p("AI suggestions below are unchanged. Rationale excerpts and selected evidence anchors are a reading aid; check the concerns on page 2 before accepting a suggestion.", "muted"))
        story.append(Spacer(1, 9))
        ordered = {item["objective_id"]: item for item in objectives}
        columns = [usable * .225, usable * .205, usable * .57]
        rows = [[p("OBJECTIVE", "bold"), p("AI SUGGESTION", "bold"), p("RATIONALE EXCERPT · EVIDENCE", "bold")]]
        for objective_id in supported:
            item = ordered[objective_id]
            depth = item.get("depth")
            recommendation = item["recommendation"]
            status_style = ParagraphStyle(
                "CompactStatus" + objective_id, parent=styles["bold"],
                textColor=ORANGE if recommendation == "needs_improvement" else (
                    MUTED if recommendation == "insufficient_evidence" else BLUE),
            )
            rationale = _sentence_excerpt(
                item.get("rationale"), rationale_limit,
                "Review the full rationale in the app before judging this objective.",
                maximum_sentences=1,
            )
            rows.append([
                [p(objective_id, "label"), p(_COMPACT_TITLES[objective_id])],
                [Paragraph(_xml(_COMPACT_RECOMMENDATIONS[recommendation]), status_style), Spacer(1, 4),
                 p("Depth: " + (depth.capitalize() if depth in DEPTH_LEVELS else "To establish"), "muted")],
                [p(rationale), Spacer(1, 5), p(_compact_references(item["evidence_refs"], index), "muted")],
            ])
        matrix = Table(rows, colWidths=columns, repeatRows=1, hAlign="LEFT")
        matrix.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), .8, LINE),
            ("LINEBELOW", (0, 1), (-1, -1), .5, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([matrix, Spacer(1, 10)])
        assistance = ASSISTANCE_LABELS.get(_string(report.get("assistance_context")), ASSISTANCE_LABELS["unknown"])
        story.append(box("Assistance and autonomy: " + assistance))

        return story
    def second_page(review_limit, question_limit):
        story = []
        story.extend([p("Before recording", "title"), p("Verify the evidence, resolve the concerns and make your own judgment.", "muted"), Spacer(1, 9)])
        review_points = analysis.get("review_points", [])
        review_points = review_points if isinstance(review_points, list) else []
        story.append(p(f"{min(3, len(review_points))} selected review priorities", "heading"))
        for number, point in enumerate(review_points[:3], 1):
            excerpt = _sentence_excerpt(point, review_limit, "Read this review point in full in the app; its context cannot be safely shortened here.")
            table = Table([[p(f"0{number}", "label"), p(excerpt)]], colWidths=[31, usable - 31])
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
            question = _sentence_excerpt(item.get("question"), question_limit, "Review this decision's full debrief question in the app.")
            story.append(KeepTogether([
                p(_compact_references(item["evidence_refs"], index, maximum=2), "label"),
                p(question), Spacer(1, 8),
            ]))
        if len(decisions) > 3:
            story.append(p(f"3 of {len(decisions)} decision prompts shown; full analysis contains the rest.", "muted"))
        story.extend([Spacer(1, 2), p("Scope to preserve", "heading")])
        story.append(p("TD1/F1/C1: simulated support, prioritization and reassessment; not real teamwork or full critical-care competence. C3/C4: recorded airway, oxygen and sedation reasoning; not hands-on airway or procedural skill. C14: use of supplied POCUS findings; not image acquisition."))
        limits = analysis.get("limits", [])
        if isinstance(limits, list):
            # Assistance is already shown once in the matrix page. Keep a distinct
            # report-specific limitation rather than repeating that global caveat.
            distinct_limit = next((value for value in limits if not re.search(r"assistance|autonomy", _string(value), re.I)), None)
            if distinct_limit:
                story.append(Spacer(1, 5))
                story.append(p("Selected analysis limit: " + _sentence_excerpt(distinct_limit, 250, "Review the analysis-specific limits in the app."), "muted"))
        story.extend([Spacer(1, 11), call_to_action(), Spacer(1, 7), p("In the app, review or edit feedback and record each objective separately. Suggestions do not add credit or save an assessment. Previously recorded judgments remain editable through the correction workflow.", "muted")])
        provenance = (
            f"Generated {_timestamp(report.get('generated_at'))} · {_string(report.get('model'))} · "
            f"Prompt {_string(report.get('prompt_version'))}\n"
            f"Source {_string(report.get('source_hash'))[:16]}… · Full generation record in the complete PDF."
        )
        story.extend([Spacer(1, 8), p(provenance, "muted")])
        story.extend([Spacer(1, 6), p("D = recorded decision and simulation time. Reflection = post-encounter evidence; it does not establish what was understood during care. Full citations, feedback and rationales remain available in the app and the full PDF.", "muted")])
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
    available = height - document.topMargin - document.bottomMargin - 12
    for rationale_limit in (390, 310, 230, 160, 90):
        page_one = first_page(rationale_limit)
        if page_height(page_one) <= available:
            break
    for review_limit, question_limit in ((550, 300), (400, 250), (300, 200), (200, 150), (90, 90)):
        page_two = second_page(review_limit, question_limit)
        if page_height(page_two) <= available:
            break
    if page_height(page_one) > available or page_height(page_two) > available:
        raise ValueError("This report metadata is too long for the concise PDF; download the full analysis.")
    story = page_one + [PageBreak()] + page_two
    document.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    return out.getvalue()


def render_faculty_brief_pdf(report, record, *, compact=True, app_url=None):
    """Render an unchanged stored brief as a concise review or the full report.

    The default is a two-page reading aid. ``compact=False`` retains complete
    model text and lets it flow across pages. The optional public ``app_url``
    adds an encounter selector link; authentication remains enforced by the app.
    """
    inputs = _validated_inputs(report, record)
    if compact:
        return _render_compact(report, record, inputs, app_url)
    return _render_full(report, record, inputs)
