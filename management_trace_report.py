"""Concise learner PDF from a validated, source-bound Management Trace analysis.

AI prose and recorded evidence are presented separately. Vitals, time labels,
action execution and learner reasoning come only from the sanitized source;
the model cannot supply a chart value. This renderer never reads faculty data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import math
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable, HRFlowable, KeepTogether, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)


import report_presentation as presentation

RENDERER_VERSION = "1.1"
NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#176C97")
ORANGE = colors.HexColor("#A95B1E")
INK = colors.HexColor("#263A49")
MUTED = colors.HexColor("#607482")
LINE = colors.HexColor("#D7E2E9")
PALE = colors.HexColor("#F1F6F9")
WARM = colors.HexColor("#FCF6ED")
TREND_FIELDS = (
    ("hr", "Heart rate", "/min"),
    ("sbp", "Systolic pressure", "mmHg"),
    ("spo2", "Oxygen saturation", "%"),
    ("respiratory_rate", "Respiratory rate", "/min"),
)
PLAN_FIELDS = (
    ("cue", "Clinical cue to watch"),
    ("threshold", "Threshold for changing course"),
    ("next_priority", "Next management priority"),
    ("alternative_action", "Alternative action"),
    ("expected_effect", "Expected effect"),
    ("reassessment_plan", "Reassessment target and timing"),
)
OBSERVED_FIELDS = (
    ("hr", "HR", "/min"), ("sbp", "SBP", "mmHg"),
    ("dbp", "DBP", "mmHg"), ("spo2", "SpO2", "%"),
    ("respiratory_rate", "RR", "/min"), ("crt", "CRT", "s"),
    ("mental_status", "Alertness", ""),
    ("work_of_breathing", "Breathing effort", ""),
    ("extremities", "Extremities", ""), ("rhythm", "Rhythm", ""),
    ("pulse_present", "Pulse present", ""),
)


def _text(value):
    return value if isinstance(value, str) else ""


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def _scalar(value):
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if _number(value) is not None:
        return f"{value:g}"
    return ""


def _xml(value):
    text = _text(value).translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return escape(text).replace("\n", "<br/>")


def _fonts():
    directory = Path(__file__).resolve().parent / "assets" / "fonts"
    for suffix, filename in (("", "Regular"), ("-Bold", "Bold"), ("-Italic", "Italic")):
        name = "TraceSans" + suffix
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(directory / f"LiberationSans-{filename}.ttf")))
    pdfmetrics.registerFontFamily(
        "TraceSans", normal="TraceSans", bold="TraceSans-Bold",
        italic="TraceSans-Italic", boldItalic="TraceSans-Bold",
    )


def _styles():
    body = ParagraphStyle(
        "TraceBody", fontName="TraceSans", fontSize=11, leading=15.4,
        textColor=INK, spaceAfter=5, splitLongWords=True,
        allowWidows=0, allowOrphans=0,
    )
    return {
        "body": body,
        "small": ParagraphStyle("TraceSmall", parent=body, fontSize=9, leading=12.5, textColor=MUTED),
        "tiny": ParagraphStyle("TraceTiny", parent=body, fontSize=7.6, leading=10, textColor=MUTED),
        "note": ParagraphStyle("TraceNote", parent=body, fontSize=9.4, leading=13, textColor=MUTED),
        "title": ParagraphStyle("TraceTitle", parent=body, fontName="TraceSans-Bold", fontSize=29, leading=32, textColor=NAVY, spaceAfter=9),
        "subtitle": ParagraphStyle("TraceSubtitle", parent=body, fontSize=12, leading=17, textColor=MUTED, spaceAfter=12),
        "heading": ParagraphStyle("TraceHeading", parent=body, fontName="TraceSans-Bold", fontSize=17, leading=21, textColor=NAVY, spaceAfter=8, keepWithNext=True),
        "card_title": ParagraphStyle("TraceCardTitle", parent=body, fontName="TraceSans-Bold", fontSize=13, leading=17, textColor=NAVY, spaceAfter=8, keepWithNext=True),
        "label": ParagraphStyle("TraceLabel", parent=body, fontName="TraceSans-Bold", fontSize=8.6, leading=11.5, textColor=BLUE, spaceBefore=6, spaceAfter=3, keepWithNext=True),
        "ai": ParagraphStyle("TraceAI", parent=body, borderColor=BLUE, borderWidth=.6, borderPadding=7, leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=10),
        "quote": ParagraphStyle("TraceQuote", parent=body, textColor=ORANGE, fontSize=8.8, leading=12, leftIndent=8, spaceAfter=6),
    }


def _time(value):
    number = _number(value)
    return f"{number:g} min" if number is not None and number >= 0 else "Time not recorded"


def _timestamp(value):
    number = _number(value)
    if number is not None:
        try:
            return datetime.fromtimestamp(number, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, OSError, OverflowError):
            return "Not recorded"
    return _text(value) or "Not recorded"


def trend_points(timeline, field):
    """Exact chronological observations; missing data break the drawn line.

    Same-time changed values are retained. Only identical consecutive samples
    collapse, with all source references retained. No resampling or smoothing.
    """
    if field not in {item[0] for item in TREND_FIELDS}:
        raise ValueError("This is not a supported observed vital sign.")
    points = []
    for event in timeline:
        for side, time_key in (("state_before", "decision_time_min"), ("state_after", "response_time_min")):
            state = _mapping(event.get(side))
            minute = _number(event.get(time_key, state.get("sim_time_min")))
            if minute is None or minute < 0:
                continue
            value = _number(_mapping(state.get("observable")).get(field))
            point = {"time_min": minute, "value": value,
                     "evidence_refs": [_text(event.get("source_ref"))]}
            if points and points[-1]["time_min"] == minute and points[-1]["value"] == value:
                if point["evidence_refs"][0] not in points[-1]["evidence_refs"]:
                    points[-1]["evidence_refs"].extend(point["evidence_refs"])
            else:
                points.append(point)
    return points


class _Trend(Flowable):
    """A vector small-multiple with a true time axis and exact endpoint labels."""

    def __init__(self, points, label, unit, width=238, height=140, markers=()):
        super().__init__()
        self.width, self.height = width, height
        self.points, self.label, self.unit = points, label, unit
        # (minute, short label) for each executed decision. Faculty request
        # 2026-09-23: a reader cannot interpret a line without knowing when
        # something was done. The marks are times, never causal claims.
        self.markers = tuple(markers)

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(PALE)
        canvas.roundRect(0, 0, self.width, self.height, 8, stroke=0, fill=1)
        canvas.setFillColor(NAVY)
        canvas.setFont("TraceSans-Bold", 9)
        canvas.drawString(12, self.height - 18, self.label)
        canvas.setFillColor(MUTED)
        canvas.setFont("TraceSans", 7.5)
        canvas.drawRightString(self.width - 12, self.height - 18, self.unit)
        available = [point for point in self.points if point["value"] is not None]
        if not available:
            canvas.drawString(12, self.height / 2, "No recorded measurements")
            canvas.restoreState()
            return
        times = [point["time_min"] for point in self.points]
        values = [point["value"] for point in available]
        first, last = min(times), max(times)
        low, high = min(values), max(values)
        padding = max((high - low) * .18, abs(high) * .025, 1)
        low_axis, high_axis = low - padding, high + padding
        x0, x1, y0, y1 = 40, self.width - 15, 30, self.height - 40

        def x(minute):
            return x0 + (minute - first) / (last - first) * (x1 - x0) if last > first else (x0 + x1) / 2

        def y(value):
            return y0 + (value - low_axis) / (high_axis - low_axis) * (y1 - y0)

        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.5)
        for value in sorted({low, high}):
            canvas.line(x0, y(value), x1, y(value))
            canvas.setFillColor(MUTED)
            canvas.drawRightString(x0 - 6, y(value) - 2, f"{value:g}")
        # When each decision was taken, under the same time axis.
        drawn = []
        for minute, mark in self.markers:
            if last > first and not first <= minute <= last:
                continue
            position = x(minute)
            if any(abs(position - taken) < 11 for taken in drawn):
                continue
            drawn.append(position)
            canvas.setStrokeColor(ORANGE)
            canvas.setLineWidth(.7)
            canvas.setDash(1, 2)
            canvas.line(position, y0 - 4, position, y1)
            canvas.setDash()
            canvas.setFillColor(ORANGE)
            canvas.setFont("TraceSans-Bold", 6.4)
            canvas.drawCentredString(position, y1 + 3, str(mark))
        canvas.setStrokeColor(BLUE)
        canvas.setLineWidth(1.7)
        previous = None
        for point in self.points:
            if point["value"] is None:
                previous = None
                continue
            if previous is not None and point["time_min"] >= previous["time_min"]:
                canvas.line(x(previous["time_min"]), y(previous["value"]), x(point["time_min"]), y(point["value"]))
            canvas.setFillColor(BLUE)
            canvas.circle(x(point["time_min"]), y(point["value"]), 2.3, stroke=0, fill=1)
            previous = point
        if len({point["value"] for point in available}) == 1 and len(available) > 1:
            canvas.setFillColor(MUTED)
            canvas.setFont("TraceSans", 6.6)
            canvas.drawString(x0, y1 + 12, "no recorded change")
        canvas.setFillColor(MUTED)
        canvas.setFont("TraceSans", 7)
        if first == last:
            canvas.drawCentredString((x0 + x1) / 2, 16, f"{first:g} min")
        else:
            canvas.drawString(x0, 16, f"{first:g} min")
            canvas.drawRightString(x1, 16, f"{last:g} min")
        canvas.restoreState()


def _action_text(action):
    """One executed action, written as an order rather than as engine fields."""
    return presentation.action_phrase(action)


def _observed_vitals(event):
    """What changed, and what did not, between the decision and its response."""
    before = _mapping(_mapping(event.get("state_before")).get("observable"))
    after = _mapping(_mapping(event.get("state_after")).get("observable"))
    changed, unchanged = [], []
    for key, label, unit in OBSERVED_FIELDS:
        left, right = _scalar(before.get(key)), _scalar(after.get(key))
        if not left and not right:
            continue
        suffix = f" {unit}" if unit else ""
        if left != right:
            changed.append(f"{label} {left or 'not recorded'} &#8594; {right or 'not recorded'}{suffix}")
        else:
            unchanged.append(f"{label} {right}{suffix}")
    return changed, unchanged


def _observed_studies(event):
    """Reports that became available during this decision's interval."""
    prior = _mapping(_mapping(event.get("state_before")).get("diagnostics_available"))
    lines = []
    for name, report in _mapping(_mapping(event.get("state_after")).get("diagnostics_available")).items():
        if not isinstance(report, dict) or report == prior.get(name):
            continue
        fields = [presentation.result_field(key, _scalar(value)) for key, value in report.items()
                  if key not in {"time_min", "collected_at_min"} and _scalar(value)]
        if not fields:
            continue
        timing = "available at " + _time(report.get("time_min"))
        if report.get("collected_at_min") is not None:
            timing += ", sampled at " + _time(report["collected_at_min"])
        lines.append((presentation.study_name(name) + " (" + timing + ")", "; ".join(fields)))
    return lines


_ECG_STUDIES = frozenset({"ecg", "ecg_right", "ecg_posterior"})


def _studies_without_a_result(event, closed_at_min=None):
    """Studies this decision ordered whose result is not in the record yet.

    Faculty request 2026-09-23: an order never written, one written and not
    executed, one still pending at the close and one whose result was never
    recorded are four different things, and only the first is a decision the
    resident did not take.
    """
    arrived = set(_mapping(_mapping(event.get("state_after")).get("diagnostics_available")))
    already = set(_mapping(_mapping(event.get("state_before")).get("diagnostics_available")))
    # An electrocardiogram's result is the tracing itself, kept with the
    # encounter rather than as a written report. Counting it as a missing result
    # would read as a gap the resident left, which it is not.
    tracings_before = len(_mapping(event.get("state_before")).get("ecg_recordings") or [])
    tracings_after = len(_mapping(event.get("state_after")).get("ecg_recordings") or [])
    lines = []
    for action in event.get("executed_actions", []) or []:
        if not isinstance(action, dict) or action.get("type") != "diagnostic":
            continue
        key = str(action.get("diagnostic") or action.get("diagnostic_type") or "")
        if not key or key in arrived - already:
            continue
        name = presentation.study_name(key)
        if key in _ECG_STUDIES:
            if tracings_after > tracings_before:
                lines.append(f"{name}: acquired; the tracing is kept with the encounter record")
            else:
                lines.append(f"{name}: requested; no tracing recorded in this interval")
            continue
        result = action.get("result") if isinstance(action.get("result"), dict) else {}
        ready = _number(result.get("time_min"))
        response = _number(event.get("response_time_min"))
        if ready is not None and response is not None and ready > response:
            lines.append(f"{name}: requested; the result was not due until {_time(ready)}")
        elif closed_at_min is not None and response is not None and response >= closed_at_min:
            lines.append(f"{name}: requested; still pending when the encounter closed")
        else:
            lines.append(f"{name}: requested; no result recorded in this interval")
    return lines


def _observed_response(event):
    """Kept for callers that want the single-paragraph form."""
    changed, unchanged = _observed_vitals(event)
    parts = []
    if changed:
        parts.append("; ".join(changed))
    if unchanged:
        parts.append("Unchanged: " + "; ".join(unchanged))
    for heading, body in _observed_studies(event):
        parts.append(heading + ": " + body)
    return ". ".join(parts) or "No before/after observations recorded."


def _all_claims(analysis):
    """Every model-written passage in the report, for counting truncations."""
    yield analysis.get("overview")
    yield analysis.get("trajectory")
    for claim in list(analysis.get("strengths") or []) + list(analysis.get("questions") or []):
        yield claim
    for moment in analysis.get("pivotal_decisions") or []:
        for key in ("interpretation", "expected_vs_observed", "adaptation", "reflection_insight"):
            if moment.get(key):
                yield moment[key]


def render_management_trace_pdf(
    report, payload, *, case_label="", learner_label="", review_completed=False,
    adaptation_plan=None,
):
    """Render a learner report; the report must match frozen source + reflection.

    ``adaptation_plan`` is later learner-authored content, not part of the AI
    input or fingerprint. Review status labels distinguish completed learning
    cycles from exports made before the comparison/adaptation is finished.
    """
    from management_trace_analysis import (
        build_analysis_source, validate_management_trace_analysis,
    )

    validate_management_trace_analysis(report, payload)
    source = build_analysis_source(payload)
    timeline = source["timeline"]
    index = {event["source_ref"]: event for event in timeline}
    reflection_index = {item["source_ref"]: item for item in source.get("reflections", [])}
    encounter_index = {item["source_ref"]: item for item in source.get("encounter_events", [])}
    analysis = report["analysis"]
    _fonts()
    styles = _styles()
    output = BytesIO()
    width, height = A4
    margin = 42
    content_width = width - 2 * margin
    document = SimpleDocTemplate(
        output, pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=49, bottomMargin=62, title="Management Trace - learner synthesis",
        author="Management Reasoning Simulator",
        subject="Source-bound AI interpretation of management decisions and observed patient response",
        pageCompression=1,
    )
    status = "REVIEW COMPLETE" if review_completed else "DRAFT - REVIEW IN PROGRESS"
    story = []

    def p(text, style="body"):
        return Paragraph(_xml(text), styles[style])

    def reference_label(ref):
        """A reference a reader can follow: what it is and when, not its id."""
        if ref in index:
            event = index[ref]
            label = f"D{event['decision_number']}" if event.get("decision_number") is not None else "Non-executed entry"
            return f"{label} at {_time(event.get('decision_time_min'))}"
        if ref in encounter_index:
            event = encounter_index[ref]
            kind = _text(event.get("kind")).replace("_", " ")
            kind = {"you": "your own order", "patient history": "history", "clinical update": "patient update",
                    "diagnostic result": "study result"}.get(kind, kind) or "encounter record"
            return f"{kind} at {_time(event.get('time_min'))}"
        reflection = reflection_index.get(ref, {})
        decision = index.get(reflection.get("decision_ref"), {})
        return f"your later reflection on D{decision.get('decision_number', '?')}"

    def claim_paragraph(claim, style="body"):
        claim = _mapping(claim)
        refs = claim.get("evidence_refs", [])
        text = _xml(presentation.claim_text(claim.get("text", "")))
        if refs:
            seen, labels = set(), []
            for ref in refs:
                label = reference_label(ref)
                if label not in seen:
                    seen.add(label)
                    labels.append(label)
            suffix = "Based on: " + ", ".join(labels)
            text += '<br/><font size="7.6" color="#607482">' + _xml(suffix) + "</font>"
        return Paragraph(text, styles[style])

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(margin, height - 33, width - margin, height - 33)
        canvas.setFont("TraceSans-Bold", 7)
        canvas.setFillColor(NAVY)
        canvas.drawString(margin, height - 25, "MANAGEMENT REASONING SIMULATOR")
        canvas.setFillColor(BLUE)
        canvas.drawRightString(width - margin, height - 25, status)
        canvas.line(margin, 49, width - margin, 49)
        canvas.setFont("TraceSans", 6.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(margin, 37, f"Learner report · AI interpretation · Renderer {RENDERER_VERSION}")
        canvas.drawString(margin, 26, "Recorded changes do not establish a treatment's causal effect.")
        canvas.drawRightString(width - margin, 31, str(doc.page))
        canvas.restoreState()

    # The analysis source deliberately drops private identity fields, so the
    # encounter id is read from the frozen payload the source was built from.
    raw_trace = payload.get("trace") if isinstance(payload, dict) else None
    case_id = _text(_mapping(_mapping((raw_trace or [{}])[0]).get("state_before")).get("case_id"))
    encounter_id = presentation.identifier(case_id, _text(case_label), fallback=_text(case_label))
    decision_marks = [(_number(event.get("decision_time_min")) or 0, f"D{event['decision_number']}")
                      for event in timeline if event.get("decision_number") is not None]

    # --- page one: what happened, how it moved, what to carry forward -------
    story.extend([
        p("YOUR MANAGEMENT, RECONSTRUCTED", "label"),
        p("Management Trace", "title"),
        p("What you did. Why you acted. What happened next.", "subtitle"),
    ])
    heading_bits = [value for value in (_text(learner_label), encounter_id) if value]
    story.append(p(" · ".join(heading_bits), "small"))
    story.append(p("AI synthesis of your recorded decisions and subsequent reflection. It is a learning report: it does not award a grade, establish competence or infer a cognitive bias. Every interpretation below is provisional until your faculty reviews it.", "small"))

    story.append(p("The encounter in perspective", "heading"))
    story.append(claim_paragraph(analysis["overview"]))

    story.append(p("Recorded patient trajectory", "heading"))
    trend_width = (content_width - 12) / 2
    charts = [_Trend(trend_points(timeline, key), label, unit, width=trend_width, markers=decision_marks)
              for key, label, unit in TREND_FIELDS]
    chart_table = Table([[charts[0], charts[1]], [charts[2], charts[3]]],
                        colWidths=[content_width / 2] * 2)
    chart_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(chart_table)
    story.append(p("Points are recorded observations; lines connect them and do not show continuous monitoring. Missing values interrupt the line, and each panel has its own vertical scale. The dashed marks are the minutes at which D1-D" + str(len(decision_marks) or 1) + " were taken: they show when you acted, and a change after a mark does not establish that the action caused it.", "tiny"))
    story.append(p("AI interpretation of the trajectory", "label"))
    story.append(claim_paragraph(analysis["trajectory"]))

    story.append(p("What to carry forward", "heading"))
    story.append(p("PATTERNS TO PRESERVE", "label"))
    for claim in analysis.get("strengths", []):
        story.append(claim_paragraph(claim))
    if not analysis.get("strengths"):
        story.append(p("No additional evidence-supported pattern was identified.", "note"))
    story.append(p("QUESTIONS FOR YOUR NEXT ENCOUNTER", "label"))
    for claim in analysis.get("questions", []):
        story.append(claim_paragraph(claim))

    # --- the decisions, each read in the order a clinician reads one --------
    story.append(PageBreak())
    story.append(p("Decisions worth revisiting", "heading"))
    story.append(p("Each decision is shown as it happened: what you had observed, how you reasoned, what you ordered, what you expected, what was recorded next, and one point to revisit. Your later reflection is kept separate, because it describes your retrospective understanding and not what you necessarily knew at the time.", "small"))

    closed_at = max((_number(event.get("response_time_min")) or 0) for event in timeline) if timeline else None
    for item in analysis["pivotal_decisions"]:
        event = index[item["decision_ref"]]
        reasoning = _mapping(event.get("recorded_reasoning"))
        composed = set(event.get("app_composed_reasoning_slots") or [])
        lines = presentation.action_lines(event.get("executed_actions", []))
        time_range = f"{_time(event.get('decision_time_min'))} to {_time(event.get('response_time_min'))}"
        changed, unchanged = _observed_vitals(event)
        studies = _observed_studies(event)
        before = _mapping(_mapping(event.get("state_before")).get("observable"))
        observed_before = "; ".join(
            f"{label} {_scalar(before.get(key))}{(' ' + unit) if unit else ''}"
            for key, label, unit in OBSERVED_FIELDS if _scalar(before.get(key)))

        story.append(KeepTogether([
            Spacer(1, 9), HRFlowable(width="100%", thickness=1, color=LINE),
            p(f"DECISION {event['decision_number']} · {time_range} · {_text(event.get('execution_status')).replace('_', ' ') or 'not recorded'}", "label"),
            p(presentation.claim_text(item["title"], presentation.TITLE_CAPS), "card_title"),
            p("1 · WHAT YOU HAD OBSERVED", "label"),
            p(observed_before or "No observations were recorded before this decision."),
        ]))
        block = [
            claim_paragraph(item["interpretation"]),
            p("2 · HOW YOU REASONED", "label"),
        ]
        reasoning_fields = (("problem_representation", "Working model"),
                            ("management_priority", "Priority"), ("rationale", "Rationale"),
                            ("preservation_goal", "Preserve"))
        recorded_any = False
        for key, label in reasoning_fields:
            value = _text(reasoning.get(key))
            if not value:
                continue
            recorded_any = True
            suffix = "" if key not in composed else ' <font size="8" color="#607482">(composed by the application from your other words, not typed by you)</font>'
            block.append(Paragraph(f"<b>{label}:</b> " + _xml(value) + suffix, styles["body"]))
        if not recorded_any:
            block.append(p("No explicit working model, priority or rationale was recorded.", "note"))
        block.append(p("3 · WHAT YOU ORDERED", "label"))
        if lines:
            for line in lines:
                block.append(Paragraph("&#8226; " + _xml(line), styles["body"]))
        else:
            block.append(p("No executed action documented.", "note"))
        story.extend(block)

        expectation = _text(reasoning.get("expected_effect")) or "No expectation was recorded, so this decision has no expectation to compare."
        plan = _text(reasoning.get("reassessment_target")) or "Not recorded."
        result_bits = []
        if changed:
            result_bits.append("<b>Changed:</b> " + "; ".join(changed))
        if unchanged:
            result_bits.append("<b>Unchanged:</b> " + "; ".join(unchanged))
        if not changed and not unchanged:
            result_bits.append("No before/after observations were recorded.")
        for heading, body in studies:
            result_bits.append(f"<b>{_xml(heading)}:</b> " + _xml(body))
        for line in _studies_without_a_result(event, closed_at):
            result_bits.append('<font color="#607482">' + _xml(line) + "</font>")
        compare = Table([
            [p("4 · WHAT YOU EXPECTED", "label"), p("5 · WHAT WAS RECORDED NEXT", "label")],
            [p(expectation), Paragraph("<br/>".join(result_bits), styles["body"])],
        ], colWidths=[content_width * .40, content_width * .60], repeatRows=1,
            splitByRow=1, splitInRow=1)
        compare.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), WARM),
            ("BACKGROUND", (1, 0), (1, -1), PALE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        plan_line = p("Recorded reassessment plan: " + plan, "note")
        panel_height = compare.wrap(content_width, height)[1] + plan_line.wrap(content_width, height)[1]
        if panel_height < height - 190:
            story.append(KeepTogether([compare, plan_line]))
        else:
            story.extend([compare, plan_line])
        story.append(claim_paragraph(item["expected_vs_observed"]))
        story.append(KeepTogether([
            p("6 · POINT TO REVISIT", "label"),
            claim_paragraph(item["adaptation"]),
        ]))
        if item.get("reflection_insight"):
            story.append(KeepTogether([
                p("YOUR LATER REFLECTION — WRITTEN AFTER THE ENCOUNTER", "label"),
                p("This is retrospective. It does not establish what you understood while deciding.", "tiny"),
                Spacer(1, 3),
                claim_paragraph(item["reflection_insight"], "ai"),
            ]))

    # --- what the learner wrote afterwards, then the metadata ---------------
    entered_plan = _mapping(adaptation_plan)
    story.append(Spacer(1, 14))
    story.append(p("Your later adaptation plan", "heading"))
    story.append(p("Written by you after the comparison. It is your own text and is not part of the AI analysis above.", "small"))
    if not any(_text(entered_plan.get(key)).strip() for key, _ in PLAN_FIELDS):
        story.append(p("Not yet recorded. Complete your comparison and adaptation plan in the app.", "body"))
    else:
        for key, label in PLAN_FIELDS:
            story.append(p(label, "label"))
            story.append(p(_text(entered_plan.get(key)) or "Not recorded."))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=.6, color=LINE))
    story.append(p("Report provenance", "label"))
    truncated = sum(1 for claim in _all_claims(analysis)
                    if presentation.was_truncated(_mapping(claim).get("text")))
    story.append(p(
        f"Encounter: {encounter_id} | Generated: {_timestamp(report.get('generated_at'))} | Model: {_text(report.get('model'))}\n"
        f"Analysis: {_text(report.get('schema_version'))} | Prompt: {_text(report.get('prompt_version'))} | Renderer: {RENDERER_VERSION}\n"
        f"Source fingerprint: {_text(report.get('source_hash'))}\n"
        "The source fingerprint binds this analysis to the frozen encounter and locked reflections. "
        "The full encounter record remains available separately."
        + (f"\n{truncated} interpretation field(s) reached the analysis length limit and are marked where they stop." if truncated else ""),
        "tiny"))
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
