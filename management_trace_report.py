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


RENDERER_VERSION = "1.0"
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
        "TraceBody", fontName="TraceSans", fontSize=9.4, leading=13,
        textColor=INK, spaceAfter=4, splitLongWords=True,
        allowWidows=0, allowOrphans=0,
    )
    return {
        "body": body,
        "small": ParagraphStyle("TraceSmall", parent=body, fontSize=8.1, leading=11, textColor=MUTED),
        "tiny": ParagraphStyle("TraceTiny", parent=body, fontSize=7, leading=9, textColor=MUTED),
        "title": ParagraphStyle("TraceTitle", parent=body, fontName="TraceSans-Bold", fontSize=29, leading=32, textColor=NAVY, spaceAfter=9),
        "subtitle": ParagraphStyle("TraceSubtitle", parent=body, fontSize=12, leading=17, textColor=MUTED, spaceAfter=12),
        "heading": ParagraphStyle("TraceHeading", parent=body, fontName="TraceSans-Bold", fontSize=17, leading=21, textColor=NAVY, spaceAfter=8, keepWithNext=True),
        "card_title": ParagraphStyle("TraceCardTitle", parent=body, fontName="TraceSans-Bold", fontSize=12, leading=16, textColor=NAVY, spaceAfter=8, keepWithNext=True),
        "label": ParagraphStyle("TraceLabel", parent=body, fontName="TraceSans-Bold", fontSize=8, leading=10.5, textColor=BLUE, spaceBefore=4, spaceAfter=3, keepWithNext=True),
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

    def __init__(self, points, label, unit, width=238, height=125):
        super().__init__()
        self.width, self.height = width, height
        self.points, self.label, self.unit = points, label, unit

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
        canvas.setFillColor(MUTED)
        canvas.setFont("TraceSans", 7)
        if first == last:
            canvas.drawCentredString((x0 + x1) / 2, 16, f"{first:g} min")
        else:
            canvas.drawString(x0, 16, f"{first:g} min")
            canvas.drawRightString(x1, 16, f"{last:g} min")
        canvas.restoreState()


def _action_text(action):
    """Format only the already projected executed action's known scalar fields."""
    label = _text(action.get("label")) or _text(action.get("type")).replace("_", " ")
    fields = (
        "agent", "dose_mg", "dose_g", "dose", "units", "route", "volume_ml",
        "fluid_type", "cumulative_ml", "device", "support_type", "flow_lpm", "rate", "rate_mcg_min", "operation",
        "mode", "ipap_cmh2o", "epap_cmh2o", "fio2_percent", "ventilator_mode",
        "pressure_cmh2o", "peep_cmh2o", "service", "destination", "diagnostic", "diagnostic_type",
        "delay_min", "duration_min", "time_min", "energy_j", "synchronized",
        "cardioversion_success", "pre_rhythm", "focus", "purpose", "old_rate", "old_units",
    )
    details = [f"{key.replace('_', ' ')}: {_scalar(action[key])}"
               for key in fields if key in action and _scalar(action[key])]
    for medication in action.get("medications", []):
        if isinstance(medication, dict):
            details.append("Medication: " + "; ".join(
                f"{key.replace('_', ' ')}: {_scalar(medication[key])}"
                for key in ("agent", "dose", "dose_mg", "dose_g", "route", "units")
                if key in medication and _scalar(medication[key])))
    return label + (" (" + "; ".join(details) + ")" if details else "")


def _observed_response(event):
    before = _mapping(_mapping(event.get("state_before")).get("observable"))
    after = _mapping(_mapping(event.get("state_after")).get("observable"))
    changed, unchanged = [], []
    for key, label, unit in OBSERVED_FIELDS:
        left, right = _scalar(before.get(key)), _scalar(after.get(key))
        if not left and not right:
            continue
        suffix = f" {unit}" if unit else ""
        if left != right:
            changed.append(f"{label}: {left or 'not recorded'} → {right or 'not recorded'}{suffix}")
        else:
            unchanged.append(f"{label}: {right}{suffix}")
    parts = []
    if changed:
        parts.append("; ".join(changed))
    if unchanged:
        parts.append("Unchanged: " + "; ".join(unchanged))
    prior_reports = _mapping(_mapping(event.get("state_before")).get("diagnostics_available"))
    for name, report in _mapping(_mapping(event.get("state_after")).get("diagnostics_available")).items():
        if not isinstance(report, dict) or report == prior_reports.get(name):
            continue
        fields = [f"{key.replace('_', ' ')}: {_scalar(value)}" for key, value in report.items()
                  if key not in {"time_min", "collected_at_min"} and _scalar(value)]
        if fields:
            timing = "Available at " + _time(report.get("time_min"))
            if report.get("collected_at_min") is not None:
                timing += "; sampled at " + _time(report["collected_at_min"])
            parts.append(name.replace("_", " ") + " (" + timing + "): " + "; ".join(fields))
    return ". ".join(parts) or "No before/after observations recorded."


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
        if ref in index:
            event = index[ref]
            label = f"D{event['decision_number']}" if event.get("decision_number") is not None else "Non-executed entry"
            return f"{label} · {_time(event.get('decision_time_min'))} [{ref}]"
        if ref in encounter_index:
            event = encounter_index[ref]
            return f"{_text(event.get('kind')).replace('_', ' ').capitalize()} · {_time(event.get('time_min'))} [{ref}]"
        reflection = reflection_index.get(ref, {})
        decision = index.get(reflection.get("decision_ref"), {})
        return f"Post-encounter reflection D{decision.get('decision_number', '?')} [{ref}]"

    def claim_paragraph(claim, style="body"):
        claim = _mapping(claim)
        refs = claim.get("evidence_refs", [])
        suffix = "Sources: " + "; ".join(reference_label(ref) for ref in refs)
        text = _xml(claim.get("text", ""))
        if refs:
            text += '<br/><font size="7" color="#607482">' + _xml(suffix) + "</font>"
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

    story.extend([
        p("YOUR MANAGEMENT, RECONSTRUCTED", "label"),
        p("Management Trace", "title"),
        p("What you did. Why you acted. What happened next.", "subtitle"),
    ])
    metadata = [value for value in (_text(learner_label), _text(case_label)) if value]
    if metadata:
        story.append(p(" · ".join(metadata), "small"))
    story.append(p("AI synthesis of your recorded decisions and subsequent reflection. This is a learning report; it does not award a grade or infer a cognitive bias.", "small"))
    story.append(p("The encounter in perspective", "heading"))
    story.append(claim_paragraph(analysis["overview"]))
    story.append(p("Recorded patient trajectory", "heading"))
    trend_width = (content_width - 12) / 2
    charts = [_Trend(trend_points(timeline, key), label, unit, width=trend_width)
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
    story.append(p("Points are recorded observations; lines connect recorded points and do not show continuous monitoring. Missing values interrupt the line. Each panel has its own vertical scale. Exact decision values follow.", "tiny"))
    story.append(p("AI interpretation of the trajectory", "label"))
    story.append(claim_paragraph(analysis["trajectory"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=.6, color=LINE))
    story.append(p("Report provenance", "label"))
    story.append(p(
        f"Generated: {_timestamp(report.get('generated_at'))} | Model: {_text(report.get('model'))}\n"
        f"Analysis: {_text(report.get('schema_version'))} | Prompt: {_text(report.get('prompt_version'))}\n"
        f"Source fingerprint: {_text(report.get('source_hash'))}\n"
        "The source fingerprint binds this analysis to the frozen encounter and locked reflections. "
        "The full encounter record remains available separately.", "tiny"))
    story.append(PageBreak())
    story.append(p("Decisions worth revisiting", "heading"))
    story.append(p("Recorded reasoning is preserved beside the AI interpretation. Later reflections describe your retrospective understanding, not what you necessarily knew during the encounter.", "small"))

    for item in analysis["pivotal_decisions"]:
        event = index[item["decision_ref"]]
        reasoning = _mapping(event.get("recorded_reasoning"))
        actions = [_action_text(action) for action in event.get("executed_actions", []) if isinstance(action, dict)]
        action_text = "; ".join(action for action in actions if action)
        if not action_text:
            action_text = "No executed action documented."
        time_range = f"{_time(event.get('decision_time_min'))} to {_time(event.get('response_time_min'))}"
        story.append(KeepTogether([
            Spacer(1, 7), HRFlowable(width="100%", thickness=1, color=LINE),
            p(f"D{event['decision_number']} · {time_range} · {event.get('execution_status', 'not recorded')} [{item['decision_ref']}]", "label"),
            p(item["title"], "card_title"),
            p("RECORDED ACTION", "label"), p(action_text),
        ]))
        story.append(p("RECORDED REASONING", "label"))
        reasoning_fields = (
            ("problem_representation", "Working model"),
            ("management_priority", "Priority"), ("rationale", "Rationale"),
            ("preservation_goal", "Preserve"),
        )
        for key, label in reasoning_fields:
            value = _text(reasoning.get(key))
            if value:
                story.append(Paragraph(f"<b>{label}:</b> " + _xml(value), styles["body"]))
        if not any(_text(reasoning.get(key)) for key, _ in reasoning_fields):
            story.append(p("No explicit working model, priority or rationale was recorded.", "small"))
        compare = Table([
            [p("YOUR RECORDED EXPECTATION", "label"), p("OBSERVED AFTER THE DECISION", "label")],
            [p(_text(reasoning.get("expected_effect")) or "No expectation recorded."), p(_observed_response(event))],
        ], colWidths=[content_width * .43, content_width * .57], repeatRows=1,
            splitByRow=1, splitInRow=1)
        compare.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), WARM),
            ("BACKGROUND", (1, 0), (1, -1), PALE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        reassessment = p("Recorded reassessment plan: " + (_text(reasoning.get("reassessment_target")) or "Not recorded."), "small")
        # Keep an ordinary comparison panel intact. Only exceptionally long
        # recorded text uses in-row splitting across pages; this also avoids a
        # repeated header with an empty row remainder at a page boundary.
        panel_height = compare.wrap(content_width, height)[1] + reassessment.wrap(content_width, height)[1]
        if panel_height < height - 150:
            story.append(KeepTogether([compare, reassessment]))
        else:
            story.extend([compare, reassessment])
        for key, label in (("interpretation", f"D{event['decision_number']} - AI INTERPRETATION"),
                           ("expected_vs_observed", "EXPECTATION AND RESPONSE - AI INTERPRETATION"),
                           ("adaptation", "MODEL / PRIORITY UPDATE - AI INTERPRETATION")):
            story.append(p(label, "label"))
            story.append(claim_paragraph(item[key]))
        if item.get("reflection_insight"):
            story.append(p("LATER REFLECTION - AI INTERPRETATION", "label"))
            story.append(claim_paragraph(item["reflection_insight"]))

    story.append(Spacer(1, 14))
    story.append(p("Carry the learning forward", "heading"))
    story.append(p("Patterns to preserve - AI interpretation", "label"))
    for claim in analysis.get("strengths", []):
        story.append(claim_paragraph(claim))
    story.append(p("Questions for your next encounter - AI generated", "label"))
    for claim in analysis.get("questions", []):
        story.append(claim_paragraph(claim))
    entered_plan = _mapping(adaptation_plan)
    story.append(p("Your later adaptation plan", "heading"))
    story.append(p("Learner-entered after reflection/comparison; kept separate from the AI analysis above.", "small"))
    if not any(_text(entered_plan.get(key)).strip() for key, _ in PLAN_FIELDS):
        story.append(p("Not yet recorded. Complete your comparison and adaptation plan in the app.", "body"))
    else:
        for key, label in PLAN_FIELDS:
            story.append(p(label, "label"))
            story.append(p(_text(entered_plan.get(key)) or "Not recorded."))
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
