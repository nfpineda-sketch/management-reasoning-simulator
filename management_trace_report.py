"""Concise learner PDF from a validated, source-bound Management Trace analysis.

AI prose and recorded evidence are presented separately. Vitals, time labels,
action execution and learner reasoning come only from the sanitized source;
the model cannot supply a chart value. This renderer never reads faculty data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
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


import record_findings as findings
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
    # Faculty request 2026-09-23: this encounter turns on perfusion, and the
    # capillary refill is the bedside sign that carried it.
    ("crt", "Capillary refill", "s"),
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


def _language_note(p, language=None):
    """Said on the page, in a document not wholly written in the reader's language."""
    from faculty_report import LANGUAGE_NOTE
    from language import current as _reader_language
    if (language or _reader_language()) == "en":
        return []
    return [p(LANGUAGE_NOTE, "tiny")]


def _t(text, language=None):
    """A whole sentence, with its values named, so Spanish can reorder them."""
    import report_language
    from language import current as _reader_language
    return report_language.t(text, language or _reader_language())


def _say(text, language=None):
    """The page furniture, which is drawn on the canvas and never sees _xml."""
    import report_language
    from language import current as _reader_language
    return report_language.t(text, language or _reader_language())


def _xml(value, language=None):
    """Make text inert inside ReportLab's paragraphs, in the reader's language.

    The single funnel every string in this document passes through, which is
    why the translation happens here rather than at two hundred call sites.
    ``report_language.t`` returns anything it does not know unchanged, so the
    model's own prose and the resident's quoted words pass through untouched --
    only the document's own words are in that table (2026-09-23).
    """
    import report_language
    from language import current as _reader_language
    text = report_language.t(_text(value), language or _reader_language())
    text = text.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
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


class _OpenDecision(Flowable):
    """A zero-height mark recording where each decision opens and closes.

    A decision that needs two pages says so on the second one, and only when
    the page holds nothing but that continuation: a page where the previous
    decision ends and the next one begins is not a continuation page. Which
    page a mark lands on is known only once the document has been laid out, so
    the document is built twice and the header reads the first pass.
    """

    def __init__(self, marks, number):
        super().__init__()
        self.width = self.height = 0
        self._marks, self._number = marks, number

    def __deepcopy__(self, memo):
        # The layout pass copies the story; the marks must still reach the
        # original list, or the second pass has nothing to read.
        return _OpenDecision(self._marks, self._number)

    def wrap(self, *args):
        return 0, 0

    def draw(self):
        self._marks.append((self.canv.getPageNumber(), self._number))


class _Trend(Flowable):
    """A vector small-multiple with a true time axis and exact endpoint labels."""

    def __init__(self, points, label, unit, width=238, height=126, markers=()):
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
            canvas.drawString(12, self.height / 2, _say("No recorded measurements"))
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
            canvas.drawString(x0, y1 + 12, _say("no recorded change"))
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


def _decision_title(item, event, stage, title_caps=presentation.TITLE_CAPS):
    """The decision's own heading, complete.

    A title cut at the schema's limit is not shown as a title. What the
    decision did is already recorded, so the heading is built from the
    executed actions instead (faculty request 2026-09-23).
    """
    written = _text(item.get("title"))
    if written and not presentation.was_truncated(written, title_caps):
        return written
    names = []
    for phrase in presentation.action_lines(event.get("executed_actions", [])):
        name = phrase.split(" · ")[0].split(";")[0]
        name = re.sub(r"\s*\(.*?\)\s*$", "", name)
        name = re.sub(r"\s+requested$", "", name)
        name = re.sub(r"\s+already in place.*$", "", name).strip()
        if name and name.lower() not in {n.lower() for n in names}:
            names.append(name)
    for study in stage.get("awaiting", []):
        name = presentation.study_name(study)
        if name.lower() not in {n.lower() for n in names}:
            names.append(name)
    if not names:
        return "Recorded decision"
    shown, extra = names[:4], len(names) - 4
    heading = shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1]
    return heading + (_t(", and {n} more").format(n=extra) if extra > 0 else "")


def _recorded_course(timeline):
    """A factual summary of the chart, for when the AI passage was cut short.

    Derived only from the recorded observations, so it states the course
    without continuing a sentence the model never finished.
    """
    if not timeline:
        return ""
    first, last = timeline[0], timeline[-1]
    start = _number(first.get("decision_time_min"))
    finish = _number(last.get("response_time_min"))
    span = (_t("{n} recorded decisions between {start:g} and {finish:g} min").format(
                n=len(timeline), start=start, finish=finish)
            if start is not None and finish is not None
            else _t("{n} recorded decisions").format(n=len(timeline)))
    opening = _mapping(_mapping(first.get("state_before")).get("observable"))
    closing = _mapping(_mapping(last.get("state_after")).get("observable"))
    moves = []
    for key, label, unit in TREND_FIELDS:
        before, after = _scalar(opening.get(key)), _scalar(closing.get(key))
        if not before and not after:
            continue
        suffix = f" {unit}" if unit else ""
        moves.append(f"{_xml(label)} {_xml(before)}{_xml(suffix)} unchanged" if before == after
                     else f"{_xml(label)} {_xml(before)} &#8594; {_xml(after)}{_xml(suffix)}")
    return _xml(span) + ". " + "; ".join(moves) + "." if moves else _xml(span) + "."


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


HISTORY_RULE = ("The patient answers what you ask, for the whole encounter. A topic you did "
                "not ask about was available to you: it is not missing from the record, it "
                "was not obtained.")


def _history_section(payload, p, styles):
    """What was asked and what was never asked about, as recorded facts.

    Not an interpretation: the questions are the resident's own words and the
    unasked topics are the ones the case authors. It appears because asking is
    not an order and therefore appears nowhere else in this document -- and
    because a decision taken without asking is a decision worth seeing
    (faculty, 2026-09-23).
    """
    import history_review
    from faculty_analysis import case_id_of
    summary = history_review.review({"payload": payload}, case_id_of({"payload": payload}))
    if not summary["offered"] and not summary["exchanges"]:
        return []
    story = [Spacer(1, 12), p("The history you took", "heading")]
    if summary["exchanges"]:
        story.append(p("WHAT YOU ASKED, AND WHAT YOU WERE TOLD", "label"))
        for item in summary["exchanges"][:40]:
            story.append(KeepTogether([
                Paragraph(_xml(f"{_time(item['minute'])} \u00b7 \u201c{item['asked']}\u201d"),
                          styles["quote"]),
                Paragraph(_xml(item["answered"]), styles["small"])]))
    else:
        story.append(p("No question was asked of the patient or the available history source "
                       "during this encounter.", "note"))
    if summary["not_named"]:
        story.append(p("AVAILABLE AND NOT ASKED ABOUT", "label"))
        story.append(p(", ".join(row["label"] for row in summary["not_named"]) + ".", "body"))
        story.append(p(HISTORY_RULE, "note"))
    return story


def _raw_event(payload, ref):
    """The stored trace entry a timeline row was built from."""
    match = re.fullmatch(r"trace:(\d+)", str(ref or ""))
    trace = (payload or {}).get("trace") or []
    if match and int(match.group(1)) < len(trace) and isinstance(trace[int(match.group(1))], dict):
        return trace[int(match.group(1))]
    return {}


def render_management_trace_pdf(
    report, payload, *, case_label="", learner_label="", review_completed=False,
    adaptation_plan=None, corrections=None,
):
    """Render a learner report; the report must match frozen source + reflection.

    ``adaptation_plan`` is later learner-authored content, not part of the AI
    input or fingerprint. Review status labels distinguish completed learning
    cycles from exports made before the comparison/adaptation is finished.
    """
    from management_trace_analysis import build_analysis_source, usable_analysis

    # A format fault in one passage withholds that passage, not the report
    # (faculty decision B3). Everything else still refuses it.
    report, withheld = usable_analysis(report, payload)
    claim_caps, title_caps = presentation.caps_for(report.get("prompt_version"))
    source = build_analysis_source(payload)
    timeline = source["timeline"]
    index = {event["source_ref"]: event for event in timeline}
    reflection_index = {item["source_ref"]: item for item in source.get("reflections", [])}
    encounter_index = {item["source_ref"]: item for item in source.get("encounter_events", [])}
    analysis = report["analysis"]
    # Recorded factual corrections to the model's own text. The saved analysis
    # is untouched; what was corrected is listed with the metadata.
    import report_corrections
    correct = presentation.CorrectionLog(
        corrections if corrections is not None else report_corrections.for_payload(payload),
        references=presentation.reference_labels(payload.get("trace") or [],
                                                 payload.get("encounter_events") or []),
        language="en")
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
    incomplete = [claim for claim in _all_claims(analysis)
                  if claim is not None and presentation.was_truncated(_mapping(claim).get("text"), claim_caps)]
    incomplete += [moment for moment in analysis.get("pivotal_decisions") or []
                   if presentation.was_truncated(moment.get("title"), title_caps)]
    status = ("AI INTERPRETATION PARTIAL" if withheld
              else "AI INTERPRETATION INCOMPLETE" if incomplete
              else "REVIEW COMPLETE" if review_completed else "DRAFT - REVIEW IN PROGRESS")
    story = []

    def p(text, style="body"):
        return Paragraph(_xml(text), styles[style])

    def reference_label(ref):
        """A reference a reader can follow: what it is and when, not its id."""
        if ref in index:
            event = index[ref]
            if event.get("decision_number") is not None:
                label = f"D{event['decision_number']}"
            elif event.get("execution_status") == "information":
                # A question or an examination is information obtained, not
                # an order that failed (2026-09-24).
                label = _t("Information obtained")
            else:
                label = _t("Non-executed entry")
            return f"{label} at {_time(event.get('decision_time_min'))}"
        if ref in encounter_index:
            event = encounter_index[ref]
            kind = _text(event.get("kind")).replace("_", " ")
            kind = {"you": "your own order", "patient history": "history", "clinical update": "patient update",
                    "diagnostic result": "study result"}.get(kind, kind) or "encounter record"
            return f"{kind} at {_time(event.get('time_min'))}"
        reflection = reflection_index.get(ref, {})
        decision = index.get(reflection.get("decision_ref"), {})
        return _t("your later reflection on D{n}").format(
            n=decision.get("decision_number", "?"))

    def claim_caveat(text):
        """A claim the record cannot settle carries the reason, in the open."""
        reasons = findings.unsettled(text, limits)
        return (p(_t("The record cannot settle this: {reason}.").format(reason=reasons[0]),
                  "tiny") if reasons else None)

    def claim_paragraph(claim, style="body"):
        claim = _mapping(claim)
        refs = claim.get("evidence_refs", [])
        text = _xml(correct(presentation.claim_text(claim.get("text", ""), claim_caps)))
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

    marks, continued_pages = [], {}

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(margin, height - 33, width - margin, height - 33)
        canvas.setFont("TraceSans-Bold", 7)
        canvas.setFillColor(NAVY)
        canvas.drawString(margin, height - 25, _say("MANAGEMENT REASONING SIMULATOR"))
        canvas.setFillColor(BLUE)
        canvas.drawRightString(width - margin, height - 25, _say(status))
        carried = continued_pages.get(doc.page)
        if carried is not None:
            canvas.setFont("TraceSans-Bold", 8.6)
            canvas.setFillColor(BLUE)
            canvas.drawString(margin, height - 47, _say("DECISION {n} · CONTINUED").format(n=carried))
        canvas.line(margin, 49, width - margin, 49)
        canvas.setFont("TraceSans", 6.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(margin, 37, _say("Learner report · AI interpretation · Renderer {v}").format(v=RENDERER_VERSION))
        canvas.drawString(margin, 26, _say("Recorded changes do not establish a treatment's causal effect."))
        canvas.drawRightString(width - margin, 31, str(doc.page))
        canvas.restoreState()

    # The analysis source deliberately drops private identity fields, so the
    # encounter id is read from the frozen payload the source was built from.
    raw_trace = payload.get("trace") if isinstance(payload, dict) else None
    case_id = _text(_mapping(_mapping((raw_trace or [{}])[0]).get("state_before")).get("case_id"))
    encounter_id = presentation.identifier(case_id, _text(case_label), fallback=_text(case_label))
    stages = findings.order_stages(raw_trace)
    limits = findings.encounter_limits(raw_trace)
    urine_line = findings.urine_statement(raw_trace)
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
    if analysis["overview"] is None or presentation.was_truncated(_mapping(analysis["overview"]).get("text"), claim_caps):
        story.append(p("The AI synthesis is not shown here: it was withheld, and the passage is kept in "
                       "the technical record at the end with the reason. What follows is read from the "
                       "record, and is not an interpretation.", "note"))
        story.append(Paragraph(_t("<b>Recorded course:</b> {course}").format(
            course=_recorded_course(timeline)), styles["body"]))
    else:
        story.append(claim_paragraph(analysis["overview"]))

    story.append(p("Recorded patient trajectory", "heading"))
    trend_width = (content_width - 12) / 2
    charts = [_Trend(trend_points(timeline, key), label, unit, width=trend_width, markers=decision_marks)
              for key, label, unit in TREND_FIELDS]
    legend_lines = []
    for event in timeline:
        if event.get("decision_number") is None:
            continue
        stage = stages.get(event["source_ref"], {"reported": [], "awaiting": []})
        elsewhere = {row["study"] for row in stage["reported"] if not row["requested_here"]}
        done = presentation.action_lines(
            [action for action in event.get("executed_actions", [])
             if not (isinstance(action, dict)
                     and str(action.get("diagnostic") or action.get("diagnostic_type") or "") in elsewhere)])
        done += [presentation.study_name(study) + " requested" for study in stage["awaiting"]]
        summary = "; ".join(done[:2]) if done else "no executed action recorded"
        if len(done) > 2:
            summary += f"; +{len(done) - 2} more"
        legend_lines.append(f'<b>D{event["decision_number"]}</b> · {_time(event.get("decision_time_min"))} — {summary}')
    legend = [p("WHAT EACH MARK WAS", "label")]
    legend += [Paragraph(_xml(line).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>"), styles["tiny"])
               for line in legend_lines]
    # Two tables rather than one, so the panels can break between rows instead
    # of jumping whole to the next page and leaving one empty behind them.
    def panel_row(cells):
        table = Table([cells], colWidths=[content_width / 2] * 2)
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return table

    story.append(panel_row([charts[0], charts[1]]))
    story.append(panel_row([charts[2], charts[3]]))
    story.append(panel_row([charts[4], legend]))
    story.append(p(_t(
        "Points are recorded observations; lines connect them and do not show continuous "
        "monitoring. Missing values interrupt the line, and each panel has its own vertical "
        "scale. The dashed marks are the minutes at which D1-D{last} were taken: they show "
        "when you acted, and a change after a mark does not establish that the action caused "
        "it.").format(last=len(decision_marks) or 1), "tiny"))
    if analysis["trajectory"] is None or presentation.was_truncated(_mapping(analysis["trajectory"]).get("text"), claim_caps):
        story.append(p("The AI reading of the trajectory is not shown here; it is kept in the technical "
                       "record at the end with the reason.", "note"))
    else:
        story.append(p("AI interpretation of the trajectory", "label"))
        story.append(claim_paragraph(analysis["trajectory"]))

    story.append(p("What to carry forward", "heading"))
    story.append(p("PATTERNS TO PRESERVE", "label"))
    for claim in analysis.get("strengths", []):
        story.append(KeepTogether([claim_paragraph(claim)]))
    if not analysis.get("strengths"):
        story.append(p("No additional evidence-supported pattern was identified.", "note"))
    story.append(p("QUESTIONS FOR YOUR NEXT ENCOUNTER", "label"))
    for claim in analysis.get("questions", []):
        block = [claim_paragraph(claim)]
        caveat = claim_caveat(correct(presentation.claim_text(_mapping(claim).get("text"))))
        if caveat:
            block.append(caveat)
        story.append(KeepTogether(block))

    # --- the history, which is a record fact and not an interpretation ------
    story += _history_section(payload, p, styles)

    # --- the decisions, each read in the order a clinician reads one --------
    story.append(Spacer(1, 12))
    story.append(p("Decisions worth revisiting", "heading"))
    story.append(p("Each decision is shown as it happened: what you had observed, how you reasoned, what you ordered, what you expected, what was recorded next, and what changed after it. Your later reflection is summarised separately by the model, because it is retrospective and does not describe what you necessarily knew at the time.", "small"))

    for item in analysis["pivotal_decisions"]:
        event = index[item["decision_ref"]]
        reasoning = _mapping(event.get("recorded_reasoning"))
        composed = set(event.get("app_composed_reasoning_slots") or [])
        stage = stages.get(item["decision_ref"], {"requested": [], "reported": [], "awaiting": []})
        # What was ordered here is what the engine understood here. A study
        # reported here but asked for earlier belongs to the response, not to
        # this list, and a study asked for here appears even when its result
        # came later (faculty request 2026-09-23).
        lines = presentation.action_lines(
            [action for action in event.get("executed_actions", [])
             if isinstance(action, dict)
             and not (action.get("diagnostic") or action.get("diagnostic_type"))])
        answered = {}
        for rows in stages.values():
            for row in rows["reported"]:
                if row["requested_at_decision"] == event["decision_number"]:
                    answered.setdefault(row["study"], row)
        for study in stage["requested"]:
            phrase = presentation.study_name(study) + " requested"
            row = answered.get(study)
            if row:
                when = []
                if row["sampled_at_min"] is not None:
                    when.append(_t("sampled at {n:g} min").format(n=row["sampled_at_min"]))
                if row["reported_at_min"] is not None:
                    when.append(_t("result at {n:g} min").format(n=row["reported_at_min"]))
                if when:
                    phrase += " · " + ", ".join(when)
            elif study in stage["awaiting"]:
                phrase += " · no result recorded"
            lines.append(phrase if phrase[:2].isupper() else phrase[:1].upper() + phrase[1:])

        time_range = f"{_time(event.get('decision_time_min'))} to {_time(event.get('response_time_min'))}"
        changed, unchanged = _observed_vitals(event)
        studies = _observed_studies(event)
        before = _mapping(_mapping(event.get("state_before")).get("observable"))
        observed_before = "; ".join(
            f"{label} {_scalar(before.get(key))}{(' ' + unit) if unit else ''}"
            for key, label, unit in OBSERVED_FIELDS if _scalar(before.get(key)))

        story.append(KeepTogether([
            Spacer(1, 9), HRFlowable(width="100%", thickness=1, color=LINE),
            _OpenDecision(marks, event["decision_number"]),
            p(f"DECISION {event['decision_number']} · {time_range} · {_text(event.get('execution_status')).replace('_', ' ') or 'not recorded'}", "label"),
            p(_decision_title(item, event, stage, title_caps), "card_title"),
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
        # Where each slot came from: your sentence, something you said earlier
        # about another decision, an answer typed into the follow-up, or the
        # application's own phrasing (faculty specification 2026-09-23, §6).
        import reasoning_provenance
        provenance = event.get("reasoning_provenance") or {}
        carried_from = event.get("interpretation_carried_from") or {}
        # The number is resolved from the stored trace, not from the source:
        # the source is fingerprinted, and older records wrote a position.
        raw_event = _raw_event(payload, event.get("source_ref"))
        raw_carried = ((raw_event.get("reasoning") or {}).get("carried_from")
                       if isinstance(raw_event.get("reasoning"), dict) else None) or carried_from

        def _origin(key):
            source = provenance.get(key) or (reasoning_provenance.COMPOSED if key in composed else "")
            if not source:
                return ""
            stated_in = presentation.carried_decision(raw_carried, payload.get("trace") or [])
            if source == reasoning_provenance.CARRIED and stated_in:
                note = _t("stated earlier, in decision {n} at {minute:g} min").format(
                    n=stated_in, minute=carried_from.get("minute") or 0)
            else:
                note = _t(reasoning_provenance.LABELS[source])
            return f' <font size="8" color="#607482">({_xml(note)})</font>'

        recorded_any = False
        for key, label in reasoning_fields:
            value = _text(reasoning.get(key))
            if not value:
                continue
            recorded_any = True
            block.append(Paragraph(f"<b>{_xml(_t(label))}:</b> " + _xml(value) + _origin(key),
                                   styles["body"]))
        if not recorded_any:
            block.append(p("No explicit working model, priority or rationale was recorded.", "note"))

        # The findings the resident named, and whether they said what those
        # findings meant. "Not stated" is the honest phrase: it says what is
        # absent from the record, not what the resident failed to notice.
        named_findings = event.get("mentioned_findings") or []
        if named_findings:
            # Which reader saw them. A model was asked here only if the faculty
            # switched that on, and a reader of this page should not have to
            # guess which of the two produced a line.
            by_model = [row for row in named_findings if row.get("source") == "model"]
            read_by = (f' <font size="8" color="#607482">({_xml(_t("some read by a model"))})</font>'
                       if by_model else "")
            # How the resident held each one. Printing "crepitantes" for
            # "sin crepitantes" prints the opposite of what they observed, and
            # a faculty member reading this document cannot tell (2026-09-24).
            polarity_words = {"absent": _t("not present"), "trend": _t("changing"),
                              "uncertain": _t("uncertain")}

            def finding_text(row):
                name = str(row.get("finding") or "")
                word = polarity_words.get(row.get("polarity"))
                return f"{name} ({word})" if word else name

            block.append(Paragraph(
                f"<b>{_xml(_t('Findings mentioned'))}:</b> "
                + _xml("; ".join(finding_text(row) for row in named_findings))
                + read_by,
                styles["body"]))
            if any(row.get("contrast") for row in named_findings):
                block.append(p(_t("The resident set these against one another."), "note"))
            linked = [row for row in named_findings if row.get("linked")]
            if linked:
                block.append(Paragraph(
                    f"<b>{_xml(_t('Link expressed'))}:</b> "
                    + _xml(_t('these findings were given as the reason: "{marker}"').format(
                        marker=str(linked[0].get("link_marker") or ""))),
                    styles["body"]))
            else:
                block.append(p(_t("Link to the interpretation: not stated."), "note"))
        elif recorded_any:
            block.append(p(_t("Findings mentioned: not stated."), "note"))
        # The order ran without these, and the omission is still part of the
        # decision. Recorded here so it is read where it happened rather than
        # inferred later from a silence (faculty decision 2026-09-23).
        unstated = [_t(str(value)) for value in (event.get("unstated_prospective_elements") or []) if value]
        if unstated:
            block.append(p(_t("Not stated before this order: {elements}.").format(
                elements="; ".join(unstated)), "note"))
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
        # Request, sample and report are three moments, and a missing result is
        # not an omission by the resident (faculty request 2026-09-23).
        for row in stage["reported"]:
            # A study asked for here already carries its times in the order
            # list; only one asked for earlier needs its provenance here.
            if row["requested_here"]:
                continue
            parts = []
            if row["sampled_at_min"] is not None:
                parts.append(_t("sampled at {n:g} min").format(n=row["sampled_at_min"]))
            if row["reported_at_min"] is not None:
                parts.append(_t("reported at {n:g} min").format(n=row["reported_at_min"]))
            if not row["requested_here"]:
                parts.append(_t("requested at decision {n}").format(
                    n=row["requested_at_decision"]))
            if parts:
                result_bits.append('<font color="#607482">'
                                   + _xml(presentation.study_name(row["study"]) + ": " + ", ".join(parts))
                                   + "</font>")
        closed = limits.get("closed_at_min")
        ending = (_t(" before the encounter closed at {n:g} min").format(n=closed)
                  if closed is not None else "")
        for study in stage["awaiting"]:
            result_bits.append('<font color="#607482">' + _xml(
                presentation.study_name(study)
                + _t(": requested; no result was recorded") + ending) + "</font>")
        if any(findings.URINE_WORDS.search(line) for line in lines):
            result_bits.append('<font color="#607482">' + _xml(urine_line) + "</font>")
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
        plan_line = p(_t("Recorded reassessment plan: {plan}").format(plan=plan), "note")
        panel_height = compare.wrap(content_width, height)[1] + plan_line.wrap(content_width, height)[1]
        if panel_height < height - 190:
            story.append(KeepTogether([compare, plan_line]))
        else:
            story.extend([compare, plan_line])
        story.append(claim_paragraph(item["expected_vs_observed"]))
        caveat = claim_caveat(correct(presentation.claim_text(
            _mapping(item["expected_vs_observed"]).get("text"))))
        if caveat:
            story.append(caveat)
        # The model's adaptation field describes what changed next. Calling it
        # a point to revisit implied a reflective question it does not contain
        # unless it actually asks one (faculty request 2026-09-23).
        adaptation_text = presentation.claim_text(_mapping(item["adaptation"]).get("text"))
        adaptation_label = ("6 · POINT TO REVISIT" if adaptation_text.rstrip().endswith("?")
                            else "6 · NEXT MANAGEMENT ADJUSTMENT")
        story.append(KeepTogether([
            p(adaptation_label, "label"),
            claim_paragraph(item["adaptation"]),
        ]))
        if item.get("reflection_insight"):
            story.append(KeepTogether([
                p("AI SUMMARY OF YOUR LATER REFLECTION", "label"),
                p("Written by the model from what you wrote after the encounter. It is retrospective and does not establish what you understood while deciding.", "tiny"),
                Spacer(1, 3),
                claim_paragraph(item["reflection_insight"], "ai"),
            ]))
        story.append(_OpenDecision(marks, None))

    # --- what the learner wrote afterwards, then the metadata ---------------
    entered_plan = _mapping(adaptation_plan)
    # The plan the learner wrote is read as one thing, so it travels as one.
    plan_block = [
        Spacer(1, 14),
        p("Your later adaptation plan", "heading"),
        p("Written by you after the comparison. It is your own text and is not part of the AI analysis above.", "small"),
    ]
    if not any(_text(entered_plan.get(key)).strip() for key, _ in PLAN_FIELDS):
        plan_block.append(p("Not yet recorded. Complete your comparison and adaptation plan in the app.", "body"))
    else:
        for key, label in PLAN_FIELDS:
            plan_block.append(p(label, "label"))
            plan_block.append(p(_text(entered_plan.get(key)) or "Not recorded."))
    story.append(KeepTogether(plan_block))

    # The metadata closes the document; it must not be left alone on a page.
    truncated = sum(1 for claim in _all_claims(analysis)
                    if claim is not None and presentation.was_truncated(_mapping(claim).get("text"), claim_caps))
    closing = [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=.6, color=LINE),
        p("Report provenance", "label"),
        *_language_note(p),
        p(
        _t("Encounter: {encounter} | Generated: {when} | Model: {model}\n"
           "Analysis: {schema} | Prompt: {prompt} | Renderer: {renderer}\n"
           "Source fingerprint: {fingerprint}\n"
           "The source fingerprint binds this analysis to the frozen encounter and locked "
           "reflections. The full encounter record remains available separately.").format(
               encounter=encounter_id, when=_timestamp(report.get("generated_at")),
               model=_text(report.get("model")), schema=_text(report.get("schema_version")),
               prompt=_text(report.get("prompt_version")), renderer=RENDERER_VERSION,
               fingerprint=_text(report.get("source_hash")))
        + ("\n" + _t("{n} interpretation field(s) reached the analysis length limit and are "
                     "marked where they stop.").format(n=truncated) if truncated else "")
        + ("\n" + _t("{n} factual correction(s) were applied to the AI text at render time; "
                     "the saved analysis keeps the original wording.").format(
                         n=len(correct.applied)) if correct.applied else ""),
        "tiny"),
    ]
    closing += [p("Correction: " + reason, "tiny") for reason in correct.lines()]
    if withheld:
        closing.append(p(_t("Technical record — {n} AI passage(s) withheld from the reading "
                            "above, kept here with the reason:").format(n=len(withheld)), "tiny"))
        for item in withheld:
            closing.append(p(_t("· {section} — withheld for {reason}: ").format(
                section=item["section"], reason=item["reason"])
                + " ".join(str(item.get("text") or "").split())[:400], "tiny"))
    if incomplete:
        closing.append(p("Technical record — AI passages that stopped at the analysis length limit and "
                         "were therefore not used in the reading above:", "tiny"))
        for claim in incomplete:
            mapped = _mapping(claim)
            if "text" in mapped:
                fragment, caps = mapped.get("text"), claim_caps
            else:
                fragment, caps = mapped.get("title"), title_caps
            closing.append(p("· " + presentation.claim_text(fragment, caps), "tiny"))
    # Pull it back beside the last plan field, label and value together, so the
    # metadata never stands on its own and no heading is left behind.
    story.append(KeepTogether(closing))
    # First pass learns the layout; the header of the second pass uses it.
    SimpleDocTemplate(
        BytesIO(), pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=49, bottomMargin=62, pageCompression=1,
    ).build(deepcopy(story), onFirstPage=footer, onLaterPages=footer)
    layout = list(marks)
    marks.clear()
    # Which decision is open when each page begins, and which decisions open on
    # it. A page that only continues one is the page that says so.
    last_page = max([page for page, _ in layout] or [1])
    by_page = {}
    for page, number in layout:
        by_page.setdefault(page, []).append(number)
    standing = None
    for page in range(1, last_page + 1):
        at_start = standing
        opened_here = [number for number in by_page.get(page, []) if number is not None]
        if at_start is not None and not opened_here:
            continued_pages[page] = at_start
        for number in by_page.get(page, []):
            standing = number
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
